"""
Audio preprocessing and feature extraction module
Handles loading, normalizing, and extracting features from audio files
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Dict, List


class AudioProcessor:
    """Processes audio files and extracts features for key generation"""
    
    def __init__(self, sr: int = 22050, n_mels: int = 128, n_fft: int = 2048):
        """
        Initialize audio processor
        
        Args:
            sr: Sample rate (default: 22050 Hz)
            n_mels: Number of mel bands (default: 128)
            n_fft: FFT window size (default: 2048)
        """
        self.sr = sr
        self.n_mels = n_mels
        self.n_fft = n_fft
    
    def load_audio(self, audio_path: str, duration: float = None) -> Tuple[np.ndarray, int]:
        """
        Load audio file
        
        Args:
            audio_path: Path to audio file
            duration: Optional duration to load in seconds
            
        Returns:
            Tuple of (audio signal, sample rate)
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.sr, duration=duration)
            return y, sr
        except Exception as e:
            raise ValueError(f"Failed to load audio: {e}")
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range"""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def split_segments(self, audio: np.ndarray, segment_length: float = 3.0) -> List[np.ndarray]:
        """
        Split audio into segments
        
        Args:
            audio: Audio signal
            segment_length: Length of each segment in seconds
            
        Returns:
            List of audio segments
        """
        segment_samples = int(segment_length * self.sr)
        if segment_samples <= 0:
            return [audio]

        segments = []
        total_samples = len(audio)

        # Step through audio in fixed windows; include exact full-length windows.
        for i in range(0, total_samples, segment_samples):
            segment = audio[i:i + segment_samples]
            if len(segment) > 0:
                segments.append(segment)

        # Fallback safeguard for extremely short/edge-case inputs.
        if not segments:
            segments = [audio]

        return segments
    
    def extract_mel_spectrogram(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract mel-spectrogram features
        
        Args:
            audio: Audio signal
            
        Returns:
            Mel-spectrogram (n_mels x time_steps)
        """
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=self.sr,
            n_mels=self.n_mels,
            n_fft=self.n_fft
        )
        # Convert to dB scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_spec_db
    
    def extract_spectral_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract spectral statistics
        
        Args:
            audio: Audio signal
            
        Returns:
            Dictionary of spectral features
        """
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=self.sr,
            n_mels=self.n_mels
        )
        
        # Compute statistics
        features = {
            'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(S=mel_spec))),
            'spectral_rolloff': float(np.mean(librosa.feature.spectral_rolloff(S=mel_spec))),
            'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(audio))),
            'energy': float(np.mean(np.abs(audio))),
            'rms_energy': float(np.sqrt(np.mean(audio ** 2)))
        }
        
        return features
    
    def process_audio_file(self, audio_path: str) -> Dict:
        """
        Complete audio processing pipeline
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with processed data
        """
        # Load audio
        audio, sr = self.load_audio(audio_path)
        
        # Normalize
        audio = self.normalize_audio(audio)
        
        # Split into segments
        segments = self.split_segments(audio, segment_length=3.0)
        
        # Extract features
        spectrograms = []
        features_list = []
        
        for segment in segments:
            mel_spec = self.extract_mel_spectrogram(segment)
            spectral_feat = self.extract_spectral_features(segment)
            
            spectrograms.append(mel_spec)
            features_list.append(spectral_feat)
        
        return {
            'audio': audio,
            'segments': segments,
            'spectrograms': spectrograms,
            'features': features_list,
            'sample_rate': sr
        }

    def save_audio(self, audio: np.ndarray, output_path: str, sr: int = None) -> str:
        """Save an audio array to disk as a wav-compatible file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(target), audio, sr or self.sr)
        return str(target)
