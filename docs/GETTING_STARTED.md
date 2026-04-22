# Getting Started with AudioKey

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `librosa` and `soundfile` for audio processing
- `torch` and `torchvision` for the ML model
- `pycryptodome` for AES encryption
- `pydantic` for data validation
- And other supporting libraries

### 2. Test the Installation

```bash
python tests/test_components.py
```

This will verify all components are working.

### 3. Train the Model (Optional)

The project includes a pre-trained model, but you can train your own:

```bash
python models/train.py
```

This will:
- Generate synthetic audio-based training data
- Train the AudioKeyCNN model
- Save the model to `models/audkeycnn_pretrained.pt`

### 4. Use the CLI

#### Generate Key from Audio

```bash
python app/cli.py generate-key path/to/audio.wav --evaluate
```

#### Generate Key with PIN

```bash
python app/cli.py generate-key path/to/audio.wav --pin "mypin123"
```

#### Show Agent Information

```bash
python app/cli.py agent-info
```

## Project Structure

```
audiokey/
├── core/                    # Core functionality
│   ├── audio_processor.py   # Audio loading and feature extraction
│   ├── keygen.py            # Cryptographic key generation
│   └── crypto/
│       └── aes_crypto.py    # AES encryption/decryption
│
├── models/                  # Machine learning components
│   ├── audkeycnn.py         # CNN model for key quality evaluation
│   └── train.py             # Training script
│
├── agent/                   # Agentic AI system (Professor's requirement!)
│   ├── key_quality_agent.py # Main agent implementation
│   │   - AudioKeyAgent: Evaluates audio for key quality
│   │   - KeyQualityRules: Expert system rules
│   │   - KeyEvaluationWorkflow: Orchestrates the pipeline
│
├── app/                     # User-facing interface
│   └── cli.py               # Command-line interface
│
├── data/                    # Data storage
│   ├── raw/                 # Original audio files
│   └── processed/           # Processed features
│
└── docs/                    # Documentation

```

## Key Components

### 1. Audio Processor (`core/audio_processor.py`)

Handles all audio preprocessing:
- Loading audio files
- Normalizing amplitude
- Splitting into segments
- Extracting mel-spectrograms
- Computing spectral features (centroid, rolloff, ZCR, energy, etc.)

**Usage:**
```python
from core import AudioProcessor

processor = AudioProcessor(sr=22050, n_mels=128)
result = processor.process_audio_file("audio.wav")
# Returns: segments, spectrograms, features
```

### 2. Key Generator (`core/keygen.py`)

Converts audio features to cryptographic keys:
- Quantizes mel-spectrograms
- Combines with optional PIN
- Generates 256-bit AES keys via SHA256

**Usage:**
```python
from core import KeyGenerator

keygen = KeyGenerator(key_length=32)
key = keygen.generate_key_from_spectrogram(mel_spec, pin="mypin")
```

### 3. AES Crypto (`core/crypto/aes_crypto.py`)

Handles encryption/decryption:
- AES-256-CBC encryption
- IV-based security
- Text and file encryption

**Usage:**
```python
from core import AESCrypto

crypto = AESCrypto()
encrypted = crypto.encrypt("Secret", key)
plaintext = crypto.decrypt(encrypted, key)
```

### 4. AudioKeyCNN Model (`models/audkeycnn.py`)

Neural network for key quality evaluation:
- 3 convolutional layers with batch normalization
- Feature extraction from mel-spectrograms
- Binary classification: Good/Weak key
- Returns confidence scores

**Architecture:**
```
Input (128 x Time) 
  → Conv2d (1→32) → BatchNorm → ReLU → MaxPool
  → Conv2d (32→64) → BatchNorm → ReLU → MaxPool
  → Conv2d (64→128) → BatchNorm → ReLU → MaxPool
  → GlobalAvgPool → FC (128→64) → FC (64→2)
  → Output: [Good, Weak] logits
```

### 5. Audio Quality Agent (`agent/key_quality_agent.py`) ⭐

**THIS IS THE AGENTIC AI COMPONENT - Your Professor's Requirement!**

This is a hybrid expert-system + ML agent that:

**Expert System Rules:**
1. **Energy Distribution Rule**: Checks if audio has uniform energy across spectrum
2. **Spectral Diversity Rule**: Evaluates frequency content variety
3. **Zero Crossing Rate Rule**: Measures audio complexity

**ML Model Integration:**
- Combines rule-based scores (60% weight) with ML predictions (40% weight)
- Provides confidence scores

**Agent Decision Making:**
```
For each audio segment:
  1. Apply expert system rules → scores
  2. Get ML model prediction
  3. Combine scores using weighted average
  4. Determine quality level (Excellent/Good/Fair/Weak/Poor)
  5. Generate recommendations and risk factors
  6. Make final ACCEPT/REJECT decision
```

**Usage:**
```python
from agent import AudioKeyAgent, AudioAnalysisResult

agent = AudioKeyAgent(ml_model=model)

# Create analysis result
analysis = AudioAnalysisResult(
    spectrogram=mel_spec,
    features=features_dict,
    timestamp="...",
    duration=3.0,
    segment_id="seg_1"
)

# Evaluate
report = agent.evaluate_audio_segment(analysis, user_pin="optional")

# Report contains:
# - quality_level: KeyQualityLevel enum
# - confidence: float (0-1)
# - recommendations: List[str]
# - risk_factors: List[str]
# - decision: "ACCEPT" or "REJECT"
```

## Complete Workflow Example

```python
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import AudioProcessor, KeyGenerator, AESCrypto
from agent import AudioKeyAgent, KeyEvaluationWorkflow
from models import AudioKeyCNN
import torch

# 1. Load audio
processor = AudioProcessor()
audio_data = processor.process_audio_file("my_audio.wav")

# 2. Setup agent
model = AudioKeyCNN(num_classes=2)
# Load pre-trained: model.load_state_dict(torch.load("models/audkeycnn_pretrained.pt"))
agent = AudioKeyAgent(ml_model=model)

# 3. Create workflow
workflow = KeyEvaluationWorkflow(agent)

# 4. Evaluate audio
from agent import AudioAnalysisResult
analysis_results = [
    AudioAnalysisResult(
        spectrogram=spec,
        features=feat,
        timestamp="...",
        duration=3.0,
        segment_id=f"seg_{i}"
    )
    for i, (spec, feat) in enumerate(
        zip(audio_data['spectrograms'], audio_data['features'])
    )
]

# 5. Run pipeline
result = workflow.run_evaluation_pipeline(analysis_results, user_pin="mypin")

# 6. Get best segment
best_idx = result['best_segment_index']
best_report = result['best_report']

print(f"Decision: {best_report.decision}")
print(f"Quality: {best_report.quality_level.name}")
print(f"Confidence: {best_report.confidence:.2%}")

# 7. Generate key from best segment
keygen = KeyGenerator(key_length=32)
best_spec = audio_data['spectrograms'][best_idx]
key = keygen.generate_key_from_spectrogram(best_spec, pin="mypin")

# 8. Encrypt
crypto = AESCrypto()
encrypted = crypto.encrypt("My Secret Data", key)
print(f"Encrypted: {encrypted['ciphertext'][:32]}...")

# 9. Decrypt
decrypted = crypto.decrypt(encrypted, key)
print(f"Decrypted: {decrypted}")
```

## What You Need To Do

### From Your End (Important!)

1. **Prepare Audio Data:**
   - Download or create some test audio files (WAV or MP3 format)
   - Place them in `data/raw/`
   - These can be:
     - Music files
     - Voice recordings
     - Ambient noise
     - Any audio content

2. **Test with Real Audio:**
   ```bash
   python app/cli.py generate-key data/raw/your_audio.wav --evaluate
   ```

3. **Understand the Agent System:**
   - Read through the agent code: `agent/key_quality_agent.py`
   - This is what you'll present to your professor
   - It demonstrates:
     - Expert system design
     - Rule-based decision making
     - ML model integration
     - Hybrid AI approaches

4. **Optional: Fine-tune Training:**
   - Modify `models/train.py` if you want different training parameters
   - Increase `num_samples` for more training data
   - Adjust `num_epochs` for longer training

5. **Optional: Add More Rules:**
   - Extend `KeyQualityRules` class with new evaluation rules
   - Examples:
     - Frequency range checks
     - Temporal dynamics analysis
     - Music genre detection (if you add Spotify data)

### What I've Already Done

✓ Created complete project structure
✓ Implemented core audio processing
✓ Built key generation system
✓ Implemented AES encryption/decryption
✓ Created AudioKeyCNN neural network model
✓ **Built the agentic AI system** (your professor's requirement)
✓ Created CLI interface
✓ Generated training scripts
✓ Created test suite
✓ Written comprehensive documentation

## Dependencies to Install

All are in `requirements.txt`:

```
numpy          # Numerical computing
librosa        # Audio processing
scipy          # Signal processing
pydub          # Audio file handling
pycryptodome   # Cryptography
torch          # Deep learning
torchvision    # Vision utilities
soundfile      # Audio I/O
matplotlib     # Plotting (optional)
pandas         # Data handling (optional)
scikit-learn   # ML utilities (optional)
```

Install all:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### Audio file format issues
- Use WAV or MP3 files
- Librosa supports most common formats
- If issues persist, convert to WAV: `ffmpeg -i input.mp3 output.wav`

### CUDA/GPU issues
- The code works on CPU by default
- If you have CUDA, it will automatically use GPU for PyTorch
- To force CPU: modify code to use `device='cpu'`

### Import errors
- Make sure you're running from the project root directory
- The CLI scripts handle path setup automatically

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Test components: `python tests/test_components.py`
3. ✅ Prepare audio files in `data/raw/`
4. ✅ Test CLI: `python app/cli.py agent-info`
5. ✅ Generate keys: `python app/cli.py generate-key data/raw/audio.wav --evaluate`
6. ✅ Train model (optional): `python models/train.py`
7. ✅ Read agent code for presentation: `agent/key_quality_agent.py`

## For Your Professor

**Show:**
1. The complete project structure (folders + files)
2. The agentic AI system in `agent/key_quality_agent.py`
3. How expert rules + ML model work together
4. Demo: `python app/cli.py generate-key data/raw/audio.wav --evaluate`
5. The evaluation reports from the agent

**Explain:**
- How the agent makes decisions
- How rules and ML predictions combine
- How this demonstrates AI concepts from T7473
- The security aspect (AES encryption)
- The extensibility (can add more rules, improve model, etc.)

---

Good luck! The project is ready to use. Let me know if you have questions!
