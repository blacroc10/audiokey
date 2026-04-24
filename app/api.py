"""FastAPI backend for AudioKey React frontend."""

from datetime import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Optional

import torch
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent import AudioAnalysisResult, AudioKeyAgent, KeyEvaluationWorkflow
from core.audio_processor import AudioProcessor
from core.crypto.aes_crypto import AESCrypto
from core.keygen import KeyGenerator
from models import AudioKeyCNN


class EncryptRequest(BaseModel):
    plaintext: str
    key_hex: str


class DecryptRequest(BaseModel):
    iv: str
    ciphertext: str
    key_hex: str


class KeyEntryCreateRequest(BaseModel):
    label: str
    key_hex: str
    source_name: Optional[str] = None
    notes: Optional[str] = None
    quality: Optional[str] = None
    decision: Optional[str] = None


class KeyEntryUpdateRequest(BaseModel):
    label: Optional[str] = None
    key_hex: Optional[str] = None
    source_name: Optional[str] = None
    notes: Optional[str] = None
    quality: Optional[str] = None
    decision: Optional[str] = None


def _load_optional_model():
    candidate_paths = [
        project_root / "models" / "audkeycnn_pretrained.pt",
        project_root / "models" / "audkeycnn_pretrained.pth",
    ]

    existing = next((p for p in candidate_paths if p.exists()), None)
    if not existing:
        return None, None

    try:
        model = AudioKeyCNN(num_classes=2)
        model.load_state_dict(torch.load(existing, map_location="cpu"))
        model.eval()
        return model, str(existing)
    except Exception:
        return None, str(existing)


jobs_lock = threading.Lock()
analysis_jobs = {}
vault_lock = threading.Lock()
audit_lock = threading.Lock()

storage_dir = project_root / "data" / "processed"
vault_file = storage_dir / "key_vault.json"
audit_log_file = storage_dir / "usage_logs.jsonl"
vault_key_file = storage_dir / ".vault_master_key"


def _ensure_storage():
    storage_dir.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _get_vault_master_secret() -> str:
    _ensure_storage()

    env_secret = os.getenv("AUDIOKEY_VAULT_MASTER_KEY")
    if env_secret and env_secret.strip():
        return env_secret.strip()

    if vault_key_file.exists():
        return vault_key_file.read_text(encoding="utf-8").strip()

    generated = uuid.uuid4().hex + uuid.uuid4().hex
    vault_key_file.write_text(generated, encoding="utf-8")
    return generated


def _get_vault_key() -> bytes:
    secret = _get_vault_master_secret()
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _encrypt_vault_entries(entries) -> dict:
    plaintext = json.dumps(entries)
    key = _get_vault_key()
    encrypted = crypto.encrypt(plaintext, key)
    return {
        "version": 2,
        "encrypted": True,
        "algorithm": "AES-256-CBC",
        "iv": encrypted["iv"],
        "ciphertext": encrypted["ciphertext"],
        "updated_at": _now_iso(),
    }


def _decrypt_vault_payload(payload: dict):
    key = _get_vault_key()
    plaintext = crypto.decrypt({"iv": payload["iv"], "ciphertext": payload["ciphertext"]}, key)
    parsed = json.loads(plaintext)
    if not isinstance(parsed, list):
        raise ValueError("Decrypted vault payload is not a list")
    return parsed


def _append_audit_log(action: str, payload: dict):
    _ensure_storage()
    entry = {
        "id": str(uuid.uuid4()),
        "time": _now_iso(),
        "action": action,
        "payload": payload,
    }
    with audit_lock:
        with audit_log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def _load_audit_logs(limit: int = 200):
    _ensure_storage()
    if not audit_log_file.exists():
        return []
    with audit_lock:
        lines = audit_log_file.read_text(encoding="utf-8").splitlines()
    parsed = []
    for line in lines[-limit:]:
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(parsed))


def _load_key_vault():
    _ensure_storage()
    if not vault_file.exists():
        return []
    with vault_lock:
        raw = vault_file.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("encrypted") is True:
            return _decrypt_vault_payload(data)
        if isinstance(data, list):
            # Legacy plaintext format support.
            return data
        return []
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def _save_key_vault(entries):
    _ensure_storage()
    encrypted_payload = _encrypt_vault_entries(entries)
    with vault_lock:
        vault_file.write_text(json.dumps(encrypted_payload, indent=2), encoding="utf-8")


def _append_event(job_id: str, message: str):
    with jobs_lock:
        job = analysis_jobs.get(job_id)
        if not job:
            return
        job["events"].append({"time": datetime.utcnow().isoformat() + "Z", "message": message})


def _set_progress(job_id: str, progress: int, state: Optional[str] = None):
    with jobs_lock:
        job = analysis_jobs.get(job_id)
        if not job:
            return
        job["progress"] = max(0, min(100, progress))
        if state:
            job["state"] = state


def _mark_failed(job_id: str, error_message: str):
    with jobs_lock:
        job = analysis_jobs.get(job_id)
        if not job:
            return
        job["state"] = "failed"
        job["error"] = error_message
        job["progress"] = 100


def _mark_completed(job_id: str, result: dict):
    with jobs_lock:
        job = analysis_jobs.get(job_id)
        if not job:
            return
        job["state"] = "completed"
        job["result"] = result
        job["progress"] = 100


def _run_pipeline(audio_path: str, pin: Optional[str], job_id: Optional[str] = None, source_name: Optional[str] = None):
    if job_id:
        _append_event(job_id, "Loading and normalizing audio.")
        _set_progress(job_id, 8, "running")

    result_dict = processor.process_audio_file(audio_path)

    analysis_results = []
    total_segments = len(result_dict["segments"])

    if job_id:
        _append_event(job_id, f"Extracted {total_segments} segment(s); starting agent evaluation.")

    for idx, (segment, spec, features) in enumerate(
        zip(
            result_dict["segments"],
            result_dict["spectrograms"],
            result_dict["features"],
        )
    ):
        analysis_results.append(
            AudioAnalysisResult(
                spectrogram=spec,
                features=features,
                timestamp="",
                duration=len(segment) / result_dict["sample_rate"],
                segment_id=f"seg_{idx}",
            )
        )

    reports = []
    for idx, analysis in enumerate(analysis_results):
        report = agent.evaluate_audio_segment(analysis, pin or None)
        reports.append(report)
        if job_id:
            step_progress = 12 + int(((idx + 1) / max(1, total_segments)) * 68)
            _set_progress(job_id, step_progress)
            _append_event(
                job_id,
                f"Segment {idx + 1}/{total_segments}: quality={report.quality_level.name}, confidence={report.confidence:.1%}.",
            )

    best_idx = max(range(len(reports)), key=lambda i: reports[i].confidence)
    best_report = reports[best_idx]

    if job_id:
        _append_event(job_id, f"Best segment selected: #{best_idx}.")
        _set_progress(job_id, 88)

    best_spec = result_dict["spectrograms"][best_idx]
    key = keygen.generate_key_from_spectrogram(best_spec, pin or None)

    if job_id:
        _append_event(job_id, "Key derivation complete.")
        _set_progress(job_id, 96)

    return {
        "key_hex": key.hex(),
        "source_name": source_name,
        "generated_at": _now_iso(),
        "segments": len(result_dict["segments"]),
        "sample_rate": result_dict["sample_rate"],
        "best_segment": best_idx,
        "quality": best_report.quality_level.name,
        "decision": best_report.decision,
        "confidence": best_report.confidence,
        "risk_factors": best_report.risk_factors,
        "recommendations": best_report.recommendations,
        "ml_model_prediction": best_report.ml_model_prediction,
        "ml_model_confidence": best_report.ml_model_confidence,
    }


def _execute_generation_job(job_id: str, audio_path: str, pin: Optional[str], source_name: Optional[str]):
    try:
        result = _run_pipeline(audio_path, pin, job_id=job_id, source_name=source_name)
        _append_event(job_id, "Pipeline finished successfully.")
        _append_audit_log(
            "generate_key",
            {
                "job_id": job_id,
                "quality": result.get("quality"),
                "decision": result.get("decision"),
                "ml_model_prediction": result.get("ml_model_prediction"),
                "source_name": result.get("source_name"),
            },
        )
        _mark_completed(job_id, result)
    except Exception as exc:  # pylint: disable=broad-except
        _append_event(job_id, f"Pipeline failed: {exc}")
        _append_audit_log("generate_key_failed", {"job_id": job_id, "error": str(exc)})
        _mark_failed(job_id, str(exc))
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


app = FastAPI(title="AudioKey API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


processor = AudioProcessor()
keygen = KeyGenerator(key_length=32)
crypto = AESCrypto()
loaded_model, loaded_model_path = _load_optional_model()
agent = AudioKeyAgent(ml_model=loaded_model)
workflow = KeyEvaluationWorkflow(agent)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/capabilities")
def capabilities():
    info = agent.get_agent_info()
    return {
        "audio_key_generation": True,
        "aes_cipher": "AES-256-CBC",
        "vault_encryption": "AES-256-CBC",
        "agentic_architecture": info.get("architecture", "Expert System + ML Hybrid"),
        "expert_rules": info.get("rules", []),
        "agentic_loop": info.get("agentic_loop", ["observe", "plan", "act", "review"]),
        "has_ml_model": info.get("has_ml_model", False),
        "loaded_model_path": loaded_model_path,
        "dataset_reference": "FSDKaggle2019",
    }


@app.post("/api/generate-key-async")
async def generate_key_async(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    pin: Optional[str] = Form(default=None),
):
    suffix = Path(audio.filename or "sample.wav").suffix or ".wav"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name

    try:
        with temp_file as out:
            shutil.copyfileobj(audio.file, out)

        job_id = str(uuid.uuid4())
        with jobs_lock:
            analysis_jobs[job_id] = {
                "job_id": job_id,
                "state": "queued",
                "progress": 2,
                "events": [{"time": datetime.utcnow().isoformat() + "Z", "message": "Job queued."}],
                "result": None,
                "error": None,
            }

        background_tasks.add_task(_execute_generation_job, job_id, temp_path, pin, audio.filename)
        return {"job_id": job_id}
    except Exception as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        audio.file.close()


@app.get("/api/generate-key-async/{job_id}")
def get_generate_key_job(job_id: str):
    with jobs_lock:
        job = analysis_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job


@app.post("/api/generate-key")
async def generate_key(audio: UploadFile = File(...), pin: Optional[str] = Form(default=None)):
    suffix = Path(audio.filename or "sample.wav").suffix or ".wav"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name

    try:
        with temp_file as out:
            shutil.copyfileobj(audio.file, out)

        result = _run_pipeline(temp_path, pin, job_id=None, source_name=audio.filename)
        _append_audit_log(
            "generate_key",
            {
                "job_id": None,
                "quality": result.get("quality"),
                "decision": result.get("decision"),
                "ml_model_prediction": result.get("ml_model_prediction"),
                "source_name": result.get("source_name"),
            },
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        audio.file.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/encrypt")
def encrypt_text(payload: EncryptRequest):
    try:
        key = bytes.fromhex(payload.key_hex.strip())
        encrypted = crypto.encrypt(payload.plaintext, key)
        _append_audit_log(
            "encrypt_text",
            {
                "plaintext_length": len(payload.plaintext),
                "key_fingerprint": payload.key_hex[:8],
            },
        )
        return encrypted
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/decrypt")
def decrypt_text(payload: DecryptRequest):
    try:
        key = bytes.fromhex(payload.key_hex.strip())
        plaintext = crypto.decrypt({"iv": payload.iv, "ciphertext": payload.ciphertext}, key)
        _append_audit_log(
            "decrypt_text",
            {
                "ciphertext_length": len(payload.ciphertext),
                "key_fingerprint": payload.key_hex[:8],
            },
        )
        return {"plaintext": plaintext}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/logs")
def get_logs(limit: int = 200):
    safe_limit = max(1, min(1000, limit))
    return {"logs": _load_audit_logs(safe_limit)}


@app.delete("/api/logs")
def clear_logs():
    _ensure_storage()
    with audit_lock:
        if audit_log_file.exists():
            audit_log_file.write_text("", encoding="utf-8")
    return {"cleared": True}


@app.get("/api/keys")
def list_saved_keys():
    entries = _load_key_vault()
    entries = sorted(entries, key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"keys": entries}


@app.post("/api/keys")
def create_saved_key(payload: KeyEntryCreateRequest):
    if len(payload.key_hex.strip()) != 64:
        raise HTTPException(status_code=400, detail="key_hex must be 64 hex characters")

    entries = _load_key_vault()
    now = _now_iso()
    entry = {
        "id": str(uuid.uuid4()),
        "label": payload.label.strip() or "Untitled Key",
        "key_hex": payload.key_hex.strip(),
        "source_name": payload.source_name,
        "notes": payload.notes,
        "quality": payload.quality,
        "decision": payload.decision,
        "created_at": now,
        "updated_at": now,
    }
    entries.append(entry)
    _save_key_vault(entries)
    _append_audit_log("save_key", {"key_id": entry["id"], "label": entry["label"]})
    return entry


@app.put("/api/keys/{key_id}")
def update_saved_key(key_id: str, payload: KeyEntryUpdateRequest):
    entries = _load_key_vault()
    index = next((i for i, item in enumerate(entries) if item.get("id") == key_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Key entry not found")

    record = entries[index]
    if payload.label is not None:
        record["label"] = payload.label.strip() or record.get("label", "Untitled Key")
    if payload.key_hex is not None:
        if len(payload.key_hex.strip()) != 64:
            raise HTTPException(status_code=400, detail="key_hex must be 64 hex characters")
        record["key_hex"] = payload.key_hex.strip()
    if payload.source_name is not None:
        record["source_name"] = payload.source_name
    if payload.notes is not None:
        record["notes"] = payload.notes
    if payload.quality is not None:
        record["quality"] = payload.quality
    if payload.decision is not None:
        record["decision"] = payload.decision

    record["updated_at"] = _now_iso()
    entries[index] = record
    _save_key_vault(entries)
    _append_audit_log("update_key", {"key_id": record["id"], "label": record["label"]})
    return record


@app.delete("/api/keys/{key_id}")
def delete_saved_key(key_id: str):
    entries = _load_key_vault()
    next_entries = [entry for entry in entries if entry.get("id") != key_id]
    if len(next_entries) == len(entries):
        raise HTTPException(status_code=404, detail="Key entry not found")
    _save_key_vault(next_entries)
    _append_audit_log("delete_key", {"key_id": key_id})
    return {"deleted": True, "key_id": key_id}
