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

## API Endpoints

Base URL: `http://localhost:8000`

- `GET /api/health`
- `GET /api/capabilities`
- `POST /api/generate-key`
- `POST /api/generate-key-async`
- `GET /api/generate-key-async/{job_id}`
- `POST /api/encrypt`
- `POST /api/decrypt`
- `GET /api/keys`
- `POST /api/keys`
- `PUT /api/keys/{key_id}`
- `DELETE /api/keys/{key_id}`
- `GET /api/logs`
- `DELETE /api/logs`

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
