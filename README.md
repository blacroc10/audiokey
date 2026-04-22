# AudioKey – Security-Based AI System for Audio-Derived Encryption Keys
---

## **Quick Start (5 Minutes)**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the System
```bash
python tests/test_components.py
```

### 3. Check Agent Info
```bash
python app/cli.py agent-info
```

### 4. Generate Key from Audio
```bash
python app/cli.py generate-key path/to/audio.wav --evaluate
```

---

## **Mini Project: AudioKey – Security‑Based AI System for Audio‑Derived Encryption Keys (Open‑Source Framework)**

### 1. Overview

**AudioKey** is a security‑focused AI project that uses **audio signals** (songs, voice notes, or ambient noise) as a basis to **generate cryptographic keys** for encrypting and decrypting user data. The system follows an open‑source philosophy: all code, models, training scripts, and documentation are released under a permissive license (e.g., MIT or Apache‑2.0), making the project **transparent, reproducible, and extensible**.

Unlike traditional password‑based or key‑file‑based encryption, **AudioKey ties the key to a user‑specific audio file**, improving usability and offering a unique “audio‑as‑key” perspective on modern cryptography. The project integrates techniques from **Artificial Intelligence (T7473)**—such as feature extraction, pattern recognition, and neural‑network modeling—into a **security‑driven workflow**, aligning with course objectives on search, planning, knowledge representation, and expert‑style decision‑making.

***

### 2. Problem Statement and Motivation

In many real‑world environments, users either:

- Forget or reuse weak passwords, or  
- Store keys in insecure locations (e.g., plain text files, cloud notes).

**AudioKey** addresses this by letting users:

- Use **audio they already own or like** (a song, a short voice note, or even a custom noise sample) as a **seed for a cryptographic key**.  
- Have an **AI model automatically evaluate** how strong and random that key is, and optionally suggest better audio segments or minor transformations.

The motivation behind the project is three‑fold:

1. **Security + usability**: Give a more intuitive alternative to typing passwords while still using strong symmetric ciphers (like AES).  
2. **AI‑integration**: Use machine‑learning models to measure and improve the cryptographic quality of audio‑derived keys.  
3. **Open‑source research base**: Provide a clean, documented, open‑source implementation that can be reused for course projects, extended research, or even higher‑level work (e.g., masters, papers, or startup prototypes).

***

### 3. Project Scope and Alignment with Course (T7473)

This project is designed for **Artificial Intelligence (T7473, CSE & IT, Level 4)** and aligns with several learning objectives:

- **Unit 1 – Introduction to AI**  
  - The project explains how AI techniques (feature extraction, pattern recognition, neural networks) are applied in a **security‑driven application**.

- **Unit 2 – Problem Solving via Search & Planning**  
  - Later extensions can use search/planning ideas to:  
    - Find the “best” audio segment for key‑generation.  
    - Dynamically adjust audio characteristics (e.g., add noise, change bitrate) to maximize key‑quality.

- **Unit 3 – Knowledge Representation & Planning**  
  - The system can be viewed as a **simple expert‑style module**:  
    - Given an audio file and some rules (e.g., randomness thresholds), it recommends whether or not to use a particular key.

- **Unit 4 – AI Techniques (Neural Networks, Feature Extraction, Pattern Recognition)**  
  - The core AI model is a **Convolutional Neural Network (CNN)** that takes mel‑spectrograms of audio and predicts key‑quality or audio class.  
  - This directly uses feature extraction, classification, and pattern‑recognition concepts from the course.

- **Unit 5 – Natural Language Processing & Expert Systems**  
  - If you extend the project, you can add:
    - NLP‑style logging or UI (e.g., “Your key is weak; try a louder segment”).  
    - A more formal **expert‑system‑like architecture** where rules and model‑predictions combine to accept/reject keys.

Thus, **AudioKey** serves not only as a **mini‑project but also as a practical demonstration** of how AI theory maps to real‑world security‑focused software.

***

### 4. Mini Project Pipeline (Step‑by‑Step Flow)

The project follows a clean, modular pipeline designed so you can implement it in small stages, experiment, and commit incrementally (ideal for GitHub Copilot / iterative development).

#### **Phase 1 – Data Preparation & Audio Preprocessing**

1. **Select and download dataset**  
   - Use the **Freesound Audio Tagging 2019 (FSDKaggle2019)** dataset (≈29,000 short clips of music, voice, noise, and effects).  
   - This dataset is:
     - Open‑source (Creative Commons‑style licenses).  
     - Already used in audio‑tagging research, making it easy to reuse features like mel‑spectrograms.

2. **Preprocess audio files**  
   - For each audio file (WAV/other):
     - Load with `librosa` or `pydub`.  
     - Normalize amplitude and resample if needed.
     - Split long files into short segments (e.g., 2–5 seconds).

3. **Extract features**  
   - Compute:
     - FFT or mel‑spectrograms.  
     - Optional statistics: energy, zero‑crossing rate, spectral centroid, etc.  
   - Save these features in a structured format:
     - Numpy arrays (`.npy`) or HDF5.
     - A CSV or JSON file linking file IDs to labels and metadata.

This gives you a **clean, feature‑ready dataset** for both:
- The **audio‑tagging / classification** task (original dataset task).  
- Your **key‑quality prediction** task (novel extension).

***

#### **Phase 2 – Key‑Generation from Audio**

1. **Design the key‑generation logic**  
   - For each audio segment:
     - Take a subset of FFT bins or mel‑spectrogram values.  
     - Quantize them into bits (e.g., by thresholding amplitudes or using statistical binning).  
   - Combine this with:
     - Optional user PIN (hashed) → ensures the key is both audio‑based and user‑specific.

2. **Derive fixed‑length key**  
   - Result should be a **128‑bit or 256‑bit key** (suitable for AES‑128/AES‑256).  
   - Use:
     - `pycryptodome` or similar to:
       - **Encrypt** text/small files with this key.  
       - **Decrypt** using the same audio segment and (optional) PIN.

3. **Implement basic CLI / Web UI (minimal first version)**  
   - Start with a **CLI script**:
     - `audio_to_key.py` → audio file → key.  
     - `encrypt.py` / `decrypt.py` → take key → encrypt/decrypt file.  
   - Later, you can wrap this in a **web UI** (e.g., Flask or Streamlit) for “upload → encrypt → download”.

This phase gives you the **core security layer** of the project: audio → key → AES encryption/decryption.

***

#### **Phase 3 – AI Model for Key‑Quality Evaluation**

1. **Define the task**  
   - Problem: Given an audio segment and its derived key, **predict how “good” the key is**:
     - Binary: `good / weak`.  
     - Or scalar: key‑quality score (0–1).

   - You can obtain labels via:
     - Simple randomness‑like tests (e.g., frequency balance, bit‑pattern checks) on the key bits.  
     - Or, use the **audio tags** from FSDKaggle2019 (music / voice / noise) as a proxy for “type‑based” key suitability.

2. **Select and train the model**  
   - Use a **CNN model** (e.g., **AudioKeyCNN**):  
     - Input: mel‑spectrogram image of the audio segment.  
     - Hidden layers: 2–3 convolutional layers + pooling → fully connected layers.  
     - Output:  
       - Key‑quality score (regression), or  
       - Binary classification (good/weak key).

   - Training:
     - Split dataset into train/validation/test.  
     - Train on your key‑quality labels (computed from randomness tests or tags).  
     - Monitor metrics: accuracy, F1‑score, or MSE depending on the task.

3. **Integrate model into the pipeline**  
   - For each segment:
     - Run `AudioKeyCNN` on its spectrogram.  
     - Get a key‑quality score or label.  
   - Use this to:
     - Recommend which audio segment to use.  
     - Suggest small audio changes (e.g., more noise, higher volume) to improve key‑quality in later extensions.

***

#### **Phase 4 – Open‑Source & Extensibility Layer**

1. **Make everything open‑source**  
   - Repository structure:
     - `data/` – dataset pointers, preprocessing scripts, generated features.  
     - `models/` – `audkeycnn.py` (model definition), `train.py`, `evaluate.py`.  
     - `core/` – `keygen.py` (audio → key), `crypto/` (AES‑based encryption/decryption).  
     - `app/` – web UI (optional: Flask/Streamlit app).  
   - Include clear `README.md`:
     - How to install dependencies.  
     - How to download and preprocess the dataset.  
     - How to train the model and run encryption/decryption.

2. **Extensibility paths (for future work)**  
   - **Biometric‑style binding**: Combine a **voice segment** with a **song segment** to create a super‑user‑specific key (voice + music).  
   - **Federated‑style key‑generation**: Allow multiple devices to derive the same key from the same audio without sending the key itself.  
   - **Cloud‑based secure storage**:
     - Store encrypted files on cloud (e.g., AWS S3, Google Drive) and only the audio key locally.  
   - **Expert‑system‑style module**:
     - Combine model predictions, rules (e.g., “do not use low‑energy segments”), and user history to decide “accept/reject this key”.

***

### 5. Suggested Model Name: **AudioKeyCNN**

You can refer to your AI model as:

> **AudioKeyCNN** – a lightweight Convolutional Neural Network that takes mel‑spectrograms of audio segments as input and outputs a **key‑quality score or label**, indicating how suitable the audio‑derived key is for cryptographic use.

This naming makes it clear that the model:

- Is **audio‑based**.  
- Relates directly to **encryption‑key quality**.  
- Is **lightweight enough** for a third‑year project and can run on CPU or small GPUs.

***

### 6. High‑Level Pipeline Diagram (Text Description for GitHub / Copilot)

You can describe the architecture as:

```text
1. USER INPUT
   └── User uploads audio file (song, voice, noise).
   └── Optional: enters a short PIN.

2. AUDIO PREPROCESSING
   ├── Load audio with `librosa` / `pydub`.
   ├── Normalize and resample.
   ├── Split into short segments (e.g., 2–5 s).
   └── Compute mel‑spectrogram or FFT features.

3. KEY GENERATION
   ├── Quantize audio features into bits.
   ├── Combine with hashed PIN (optional) to form 128/256‑bit key.
   └── Use this key with AES to encrypt/decrypt text or small files.

4. AI MODEL (AudioKeyCNN)
   ├── Feed mel‑spectrogram of segment to AudioKeyCNN.
   ├── Model predicts key‑quality score or label.
   └── Suggest better segments or transformations if needed.

5. STORAGE & INTERFACE
   ├── Store encrypted data + metadata on disk or cloud.
   └── CLI / Web UI (Flask/Streamlit) for:
       - Upload audio.
       - View key‑quality score.
       - Perform encryption/decryption.

6. OPEN‑SOURCE LAYER
   ├── Dataset: FSDKaggle2019 + any custom audio (under open license).
   └── Code, models, training scripts, and docs released under open‑source license.
```

***

### 7. How to Use This in GitHub / Copilot

You can paste this into:

- `README.md` (as a **project overview + pipeline section**).  
- A **`docs/` folder** (e.g., `pipeline.md`, `model_design.md`) for detailed design notes.  
- Your **GitHub Copilot prompt** text (e.g., “Follow this pipeline to implement AudioKey step by step in Python”).

If you want, the next step can be a **concrete code‑structure outline** (folder + file names) that you can directly copy into your GitHub repo.
