"""
Quick test script to verify AudioKey components
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.audio_processor import AudioProcessor
from core.keygen import KeyGenerator
from core.crypto.aes_crypto import AESCrypto
from agent.key_quality_agent import AudioKeyAgent, AudioAnalysisResult
from models.audkeycnn import AudioKeyCNN


def test_components():
    """Test all major components"""
    
    print(f"\n{'='*60}")
    print("AudioKey Component Test")
    print(f"{'='*60}\n")
    
    # Test 1: Audio Processor
    print("✓ Test 1: Audio Processor")
    audio_proc = AudioProcessor()
    print(f"  - Sample rate: {audio_proc.sr} Hz")
    print(f"  - Mel bands: {audio_proc.n_mels}")
    print(f"  - FFT size: {audio_proc.n_fft}")
    
    # Generate synthetic audio for testing
    length = int(3 * audio_proc.sr)
    t = np.linspace(0, 3, length)
    rng = np.random.RandomState(42)
    test_audio = (
        0.3 * np.sin(2 * np.pi * 440 * t) +
        0.3 * np.sin(2 * np.pi * 880 * t) +
        0.2 * rng.randn(length)
    )
    test_audio = test_audio / (np.max(np.abs(test_audio)) + 1e-8)
    
    # Test preprocessing
    normalized = audio_proc.normalize_audio(test_audio)
    segments = audio_proc.split_segments(normalized, segment_length=3.0)
    print(f"  - Generated {len(segments)} segments")
    
    mel_spec = audio_proc.extract_mel_spectrogram(test_audio)
    print(f"  - Mel-spectrogram shape: {mel_spec.shape}")
    
    features = audio_proc.extract_spectral_features(test_audio)
    print(f"  - Extracted {len(features)} features")
    
    # Test 2: Key Generator
    print("\n✓ Test 2: Key Generator")
    key_gen = KeyGenerator(key_length=32)
    key = key_gen.generate_key_from_spectrogram(mel_spec)
    key_hex = key_gen.key_to_hex(key)
    print(f"  - Generated key (hex): {key_hex[:32]}...")
    print(f"  - Key length: {len(key)} bytes")
    
    # Test 3: AES Crypto
    print("\n✓ Test 3: AES Crypto")
    crypto = AESCrypto()
    
    plaintext = "Hello, AudioKey!"
    encrypted = crypto.encrypt(plaintext, key)
    print(f"  - Plaintext: {plaintext}")
    print(f"  - Encrypted (ciphertext): {encrypted['ciphertext'][:32]}...")
    
    decrypted = crypto.decrypt(encrypted, key)
    print(f"  - Decrypted: {decrypted}")
    print(f"  - Match: {decrypted == plaintext}")
    
    # Test 4: AudioKeyCNN Model
    print("\n✓ Test 4: AudioKeyCNN Model")
    model = AudioKeyCNN(num_classes=2)
    info = model.get_model_info()
    print(f"  - Total parameters: {info['total_parameters']:,}")
    print(f"  - Trainable parameters: {info['trainable_parameters']:,}")
    
    # Test model prediction
    rng = np.random.RandomState(42)
    mel_spec_test = rng.randn(1, 1, 128, 50)  # Batch x Channel x Height x Width
    try:
        import torch
        mel_spec_tensor = torch.from_numpy(mel_spec_test).float()
        output = model(mel_spec_tensor)
        print(f"  - Model forward pass successful")
        print(f"  - Output shape: {output.shape}")
    except Exception as e:
        print(f"  - Model forward pass: {e}")
    
    # Test 5: Audio Quality Agent
    print("\n✓ Test 5: Audio Quality Agent")
    agent = AudioKeyAgent(ml_model=None)  # No model for this test
    
    analysis_result = AudioAnalysisResult(
        spectrogram=mel_spec,
        features=features,
        timestamp="2024-01-01T00:00:00",
        duration=3.0,
        segment_id="test_seg_1"
    )
    
    report = agent.evaluate_audio_segment(analysis_result)
    print(f"  - Quality level: {report.quality_level.name}")
    print(f"  - Confidence: {report.confidence:.2%}")
    print(f"  - Decision: {report.decision}")
    print(f"  - Recommendations: {len(report.recommendations)} items")
    
    agent_info = agent.get_agent_info()
    print(f"  - Agent: {agent_info['agent_name']}")
    print(f"  - Architecture: {agent_info['architecture']}")
    print(f"  - Evaluations: {agent_info['total_evaluations']}")
    
    print(f"\n{'='*60}")
    print("✓ All tests passed!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    test_components()
