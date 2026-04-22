**Demo Flow (3 minutes)**
1. Start in project root and activate venv.
2. Show that tests pass.
3. Show agentic AI module.
4. Run key generation + evaluation on one audio file.
5. Explain hybrid decision logic (rules + ML).
6. Close with security output (AES-ready 256-bit key).

**Terminal Commands (copy-paste in order)**
```powershell
cd C:\Users\Shubhankar\Downloads\SIT\TYCS\audiokey
.\.venv\Scripts\Activate.ps1
python tests/test_components.py
python app/cli.py agent-info
python app/cli.py generate-key data/raw/your_audio.wav --evaluate
```

If you want to also show PIN-augmented security:
```powershell
python app/cli.py generate-key data/raw/your_audio.wav --pin "1234" --evaluate
```

**What to Say While Running**
1. “This is an AI + security mini-project where audio is transformed into a 256-bit cryptographic key.”
2. “The system first preprocesses audio, extracts mel-spectrogram and spectral features, then evaluates key quality.”
3. “This evaluation is agentic: an expert-rule engine plus a neural model combine to make an ACCEPT/REJECT decision.”
4. “After selecting the best segment, a deterministic AES-compatible key is generated.”
5. “So this is practical AI: decision intelligence, explainable recommendations, and real encryption utility.”

**Where to Point in Code (for viva questions)**
- Agent logic: key_quality_agent.py
- CLI workflow: cli.py
- Audio preprocessing: audio_processor.py
- Key derivation: keygen.py
- AES crypto: aes_crypto.py
- CNN model: audkeycnn.py

**30-second “Agentic AI” explanation**
“The agent applies three expert rules (energy distribution, spectral diversity, zero-crossing complexity), optionally combines that with CNN prediction confidence, computes a weighted score, assigns a quality level, and outputs recommendations plus an ACCEPT/REJECT action. That is autonomous decision behavior, not just static inference.”

**Before your demo**
1. Keep one short audio file ready in raw.
2. Replace your_audio.wav in command with actual filename.
3. Keep key_quality_agent.py open for quick code reference.

If you want, I can now give you a 1-page viva Q&A sheet (likely professor questions + best answers).