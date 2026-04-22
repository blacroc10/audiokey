# AudioKey Project - Visual Architecture & Summary

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (You!)                              │
│  Provides: Audio Files + Presentation to Professor              │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
   ┌─────────────┐              ┌──────────────────┐
   │ Audio Files │              │ CLI Interface    │
   │ (MP3, WAV)  │              │ (app/cli.py)     │
   └─────────────┘              └──────────────────┘
        │                               ▲
        │                               │
        └───────────┬────────┬──────────┘
                    │        │
                    ▼        ▼
         ┌─────────────────────────────┐
         │   Audio Processor           │
         │  core/audio_processor.py    │
         │                             │
         │ • Load audio (librosa)      │
         │ • Normalize                 │
         │ • Extract mel-spectrograms  │
         │ • Compute 5 features        │
         └──────────┬──────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────┐
    │   ⭐ AGENTIC AI SYSTEM ⭐             │
    │  agent/key_quality_agent.py           │
    │                                       │
    │  ┌──────────────────────────────┐    │
    │  │ Expert System Rules:         │    │
    │  │ • Energy Distribution        │    │
    │  │ • Spectral Diversity         │    │
    │  │ • Zero Crossing Rate         │    │
    │  └──────────────────────────────┘    │
    │                                       │
    │  ┌──────────────────────────────┐    │
    │  │ ML Model: AudioKeyCNN        │    │
    │  │ • 3 Conv layers              │    │
    │  │ • 116K parameters            │    │
    │  │ • Predicts: Good/Weak        │    │
    │  └──────────────────────────────┘    │
    │                                       │
    │  DECISION LOGIC:                      │
    │  score = 0.6*rules + 0.4*ml_pred    │
    │                                       │
    │  Output: Quality Level + Decision    │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Key Generator       │
    │  core/keygen.py      │
    │                      │
    │ Spectrogram → Key    │
    │ 256-bit (AES)        │
    │ Optional: + PIN      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  AES Crypto          │
    │  core/crypto/        │
    │  aes_crypto.py       │
    │                      │
    │ Encrypt/Decrypt      │
    │ Text & Files         │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Encrypted Data      │
    │  (Ready to Use!)     │
    └──────────────────────┘
```

---

## 📊 Component Breakdown

### 1. Audio Processor Module
```
INPUT: Audio File (MP3, WAV, etc.)
│
├─ Load with librosa
├─ Normalize amplitude
├─ Split into 3-second segments
├─ Extract mel-spectrograms (128 bands)
│
OUTPUT: Processed Audio Data
│
├─ Segments: List[np.ndarray]
├─ Spectrograms: List[np.ndarray]  (128 × time)
└─ Features: List[Dict]
   ├─ Spectral Centroid
   ├─ Spectral Rolloff
   ├─ Zero Crossing Rate
   ├─ Energy
   └─ RMS Energy
```

### 2. Agentic AI System ⭐
```
EVALUATION PIPELINE:

For each audio segment:

Step 1: Apply Expert System Rules
├─ Energy Distribution Rule
│  ├─ Check energy uniformity
│  ├─ Score: 0-1
│  └─ Output: Score + Reason
│
├─ Spectral Diversity Rule
│  ├─ Check frequency variety
│  ├─ Score: 0-1
│  └─ Output: Score + Reason
│
└─ Zero Crossing Rate Rule
   ├─ Check complexity
   ├─ Score: 0-1
   └─ Output: Score + Reason

Step 2: Get ML Model Prediction
├─ Feed spectrogram to AudioKeyCNN
├─ Classification: Good (0.9) or Weak (0.5)
└─ Output: Prediction + Confidence

Step 3: Combine Scores
├─ Rule-based average: mean(energy, diversity, zcr)
├─ ML model score: Convert prediction to 0-1
├─ Combined: 0.6*rules + 0.4*ml_pred
└─ Result: Final confidence (0-1)

Step 4: Map to Quality Level
├─ >= 0.80: EXCELLENT → ACCEPT
├─ >= 0.65: GOOD → ACCEPT
├─ >= 0.50: FAIR → ACCEPT
├─ >= 0.35: WEAK → REJECT
└─ < 0.35:  POOR → REJECT

Step 5: Generate Report
├─ Quality Level (enum)
├─ Confidence (0-1)
├─ Recommendations (List[str])
├─ Risk Factors (List[str])
└─ Decision (ACCEPT/REJECT)
```

### 3. Key Generator Module
```
INPUT: Mel-spectrogram + Optional PIN

Process:
├─ Quantize spectrogram to 0-255
├─ Flatten to byte sequence
├─ Combine with PIN hash (if provided)
├─ Apply SHA256 hashing
└─ Extract first 32 bytes

OUTPUT: 256-bit AES Key (32 bytes)
```

### 4. AES Crypto Module
```
ENCRYPTION:
Input: Plaintext + Key (32 bytes)
├─ Generate random IV (16 bytes)
├─ Encrypt with AES-256-CBC
├─ Pad plaintext (PKCS7)
└─ Output: IV + Ciphertext (both hex)

DECRYPTION:
Input: Ciphertext dict + Key (32 bytes)
├─ Extract IV + ciphertext (from hex)
├─ Decrypt with AES-256-CBC
├─ Remove padding
└─ Output: Plaintext
```

---

## 🎯 Key Features

### Security ✅
- AES-256-CBC encryption (military-grade)
- Random IV per encryption
- 256-bit keys from audio
- Optional PIN for additional security

### AI/ML ✅
- Expert system (rule-based decisions)
- Neural network (learned patterns)
- Hybrid approach (combining both)
- Quality evaluation for generated keys

### Usability ✅
- CLI interface (easy to use)
- Clear error messages
- Visual feedback
- Extensible architecture

### Testing ✅
- Component tests (all passing)
- Integration tests
- Synthetic data generation
- Example workflows

---

## 📈 Data Flow Examples

### Example 1: Generate Key from Audio
```
$ python app/cli.py generate-key data/raw/music.mp3 --evaluate

1. Load music.mp3
2. Split into segments
3. For each segment:
   a. Extract mel-spectrogram
   b. Extract features
   c. Run agent evaluation
   d. Get quality score
4. Select best segment
5. Generate 256-bit key
6. Display results

OUTPUT:
Quality: GOOD
Confidence: 87%
Key: a3484e94...
Decision: ACCEPT ✓
```

### Example 2: Encryption Workflow
```
Key: a3484e94... (from above)

$ python app/cli.py encrypt-text "Secret data" a3484e94...

1. Take plaintext: "Secret data"
2. Use key: a3484e94...
3. Generate random IV
4. Encrypt with AES-256-CBC
5. Output IV + ciphertext (hex)

Result can be stored or transmitted safely!
```

---

## 🧩 Module Dependencies

```
tests/test_components.py
├─ imports core modules
├─ imports models
└─ imports agent

app/cli.py
├─ imports core (AudioProcessor, KeyGenerator, AESCrypto)
├─ imports agent (AudioKeyAgent, AudioAnalysisResult, KeyEvaluationWorkflow)
└─ imports models (AudioKeyCNN)

agent/key_quality_agent.py
├─ uses AudioAnalysisResult (data class)
├─ uses KeyQualityRules (expert system)
└─ uses ML model (optional)

models/train.py
├─ uses AudioKeyCNN
└─ generates synthetic data

core/audio_processor.py
└─ uses librosa & scipy

core/keygen.py
└─ uses Crypto.Hash

core/crypto/aes_crypto.py
└─ uses pycryptodome
```

---

## 📋 File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| audio_processor.py | 180 | Audio loading & features |
| keygen.py | 140 | Key generation |
| aes_crypto.py | 180 | Encryption/decryption |
| audkeycnn.py | 200 | Neural network model |
| key_quality_agent.py | 350 | **Agentic AI system** |
| cli.py | 300 | Command-line interface |
| train.py | 250 | Training script |
| test_components.py | 150 | Test suite |
| **TOTAL** | **~1800** | **Production code** |

---

## 🎓 Concepts Demonstrated

### For Your Professor:

**AI Concepts from T7473:**
- ✅ Unit 1: AI Introduction - Practical system using AI
- ✅ Unit 2: Search & Planning - Agent decision-making
- ✅ Unit 3: Knowledge Representation - Expert system rules
- ✅ Unit 4: Neural Networks - CNN for classification
- ✅ Unit 4: Feature Extraction - Mel-spectrograms, statistics
- ✅ Unit 4: Pattern Recognition - Audio quality assessment
- ✅ Unit 5: Expert Systems - Hybrid agent architecture

**Software Engineering:**
- ✅ Modular design
- ✅ Clean architecture
- ✅ Error handling
- ✅ Type hints
- ✅ Documentation
- ✅ Test-driven development
- ✅ Extensible framework

**Real-World Application:**
- ✅ Security (cryptography)
- ✅ Audio processing (DSP)
- ✅ Machine learning (practical use)
- ✅ Decision systems (AI agents)

---

## 🚀 Quick Start Commands

```bash
# Install (if not done)
pip install -r requirements.txt

# Test everything works
python tests/test_components.py

# See agent info
python app/cli.py agent-info

# Generate key from audio
python app/cli.py generate-key data/raw/audio.wav --evaluate

# With PIN
python app/cli.py generate-key data/raw/audio.wav --pin "secret" --evaluate

# Train model (optional)
python models/train.py
```

---

## 📌 Important Notes

### What's Implemented ✅
- All core functionality
- Agentic AI system (expert + ML)
- CLI interface
- Testing suite
- Complete documentation
- Training pipeline

### What You Provide 📝
- Audio files for testing
- Time to understand the code
- Presentation to professor

### What's Optional 🎁
- Pre-trained model (can train yourself)
- GUI interface (CLI is sufficient)
- Extended features (easy to add)
- More data samples (synthetic data included)

---

## 🎯 Success Metrics

✅ **Installation:** All dependencies installed
✅ **Testing:** All tests passing
✅ **Functionality:** CLI commands working
✅ **AI Component:** Agent making decisions
✅ **Security:** Encryption/decryption working
✅ **Documentation:** Complete and clear
✅ **Code Quality:** Professional, well-organized
✅ **Extensibility:** Easy to modify/extend

---

## 🏆 You're Ready!

The AudioKey project is **fully implemented, tested, and ready to use**.

**All components working:**
- ✅ Audio processing
- ✅ Key generation
- ✅ Encryption/decryption
- ✅ Agentic AI evaluation
- ✅ Command-line interface
- ✅ Model training

**Next step:** Add audio files and test the system!

```bash
cd c:\Users\Shubhankar\Downloads\SIT\TYCS\audiokey
python app/cli.py agent-info
```

Good luck with your project and presentation! 🚀
