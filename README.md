# AudioKey

AudioKey is a Python-first system that derives AES keys from audio features, evaluates segment quality with an agent (and optional CNN model), and exposes both CLI and FastAPI interfaces with a React frontend.

## Tech Stack

- Python 3.9+
- Audio processing: `librosa`, `numpy`, `scipy`, `pydub`, `soundfile`
- Cryptography: `pycryptodome` (AES-256-CBC)
- ML: `torch`, `torchvision` (`AudioKeyCNN`)
- Backend API: `FastAPI`, `uvicorn`, `pydantic`
- Frontend: `React 18` + `Vite`
- Testing: `pytest` (plus direct component test script)

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run component sanity checks

```bash
python tests/test_components.py
```

### 3. Show agent capabilities

```bash
python app/cli.py agent-info
```

### 4. Generate a key from audio

```bash
python app/cli.py generate-key path/to/audio.wav
```

Optional flags:

```bash
python app/cli.py generate-key path/to/audio.wav --pin "1234"
python app/cli.py generate-key path/to/audio.wav --no-evaluate
python app/cli.py generate-key path/to/audio.wav --save-processed --processed-dir data/processed
```

## Run the Full App (API + Frontend)

### Terminal 1: FastAPI backend

```bash
uvicorn app.api:app --reload --port 8000
```

### Terminal 2: React frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` and calls backend on `http://localhost:8000`.

## CLI Commands

```bash
# Generate key
python app/cli.py generate-key <audio_file> [--pin PIN] [--no-evaluate]

# Encrypt text
python app/cli.py encrypt-text "hello" <key_hex>

# Decrypt text
python app/cli.py decrypt-text <ciphertext_hex> <iv_hex> <key_hex>

# Agent info
python app/cli.py agent-info
```

## Purpose

AudioKey is built to make encryption key generation more practical and user-driven by deriving keys from audio content instead of manually managed passwords or key files.

Primary goals:

- Derive deterministic 256-bit keys from audio features.
- Evaluate whether a segment is suitable for key generation before use.
- Provide both CLI and web-based workflows for real usage.
- Keep generated key operations auditable with local key-vault and usage logs.

## Potential Use Cases

- Personal secure notes or file snippets where users prefer audio-based keying material.
- Classroom/lab demonstrations of AI + cybersecurity integration.
- Prototyping adaptive key selection pipelines using audio quality signals.
- Local-first secure tooling where keys are not hardcoded in scripts.
- Research baselines for comparing rule-based vs model-assisted key quality assessment.

## Evaluation

AudioKey includes an agentic quality-evaluation loop that runs before final key selection.

How it works:

1. The input audio is normalized, segmented, and converted to spectrogram/features.
2. Each segment is evaluated by the agent using expert rules and optional `AudioKeyCNN` inference.
3. The workflow compares segment reports and selects the best candidate.
4. A final decision package is produced, including quality, confidence, risk factors, and recommendations.
5. Key derivation runs on the selected segment.

What you see in practice:

- CLI: `python app/cli.py generate-key <audio_file>` prints quality results, risk factors, and recommendations before key output.
- CLI (with trace): running generation with evaluation shows agent trace entries for decision stages.
- Backend workflow: the same agentic pipeline is used by the FastAPI service, including asynchronous job progression and decision metadata.

Why it matters:

- Reduces weak-segment key generation.
- Gives explainability (decision + confidence + risks) instead of opaque key output.
- Supports fallback behavior: if no pretrained model is available, rule-based evaluation still works.

## Model Training

Train the CNN model (synthetic dataset pipeline in current implementation):

```bash
python models/train.py
```

The trained weights are saved to `models/audkeycnn_pretrained.pt`.

## Project Layout

```text
agent/        Agentic quality evaluation workflow
app/          CLI and FastAPI app
core/         Audio processing, key derivation, AES crypto
models/       AudioKeyCNN model and training script
frontend/     React + Vite client
tests/        Component-level tests
data/         Processed artifacts, key vault, logs
docs/         Setup and project documentation
```

## Notes

- If `models/audkeycnn_pretrained.pt` is missing, CLI/API still works with rule-based evaluation.
- Generated key vault and usage logs are stored in `data/processed/`.
