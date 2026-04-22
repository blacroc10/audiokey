"""
Key generation module
Converts audio features to cryptographic keys
"""

import numpy as np
import hashlib
from typing import Tuple, Optional
from Crypto.Hash import SHA256


class KeyGenerator:
    """Generates cryptographic keys from audio features"""
    
    def __init__(self, key_length: int = 32):
        """
        Initialize key generator
        
        Args:
            key_length: Length of generated key in bytes (default: 32 = 256-bit)
        """
        self.key_length = key_length  # 32 bytes = 256 bits
    
    def quantize_spectrogram(self, mel_spectrogram: np.ndarray, bins: int = 256) -> np.ndarray:
        """
        Quantize spectrogram values to discrete bins
        
        Args:
            mel_spectrogram: Mel-spectrogram feature matrix
            bins: Number of quantization bins
            
        Returns:
            Quantized spectrogram
        """
        # Normalize to [0, bins-1]
        min_val = np.min(mel_spectrogram)
        max_val = np.max(mel_spectrogram)
        
        if max_val == min_val:
            normalized = np.zeros_like(mel_spectrogram)
        else:
            normalized = (mel_spectrogram - min_val) / (max_val - min_val)
        
        quantized = (normalized * (bins - 1)).astype(np.uint8)
        return quantized
    
    def spectrogram_to_bits(self, mel_spectrogram: np.ndarray) -> bytes:
        """
        Convert spectrogram to bit sequence
        
        Args:
            mel_spectrogram: Mel-spectrogram feature matrix
            
        Returns:
            Bytes representation
        """
        quantized = self.quantize_spectrogram(mel_spectrogram, bins=256)
        # Flatten and convert to bytes
        bits = quantized.flatten().tobytes()
        return bits
    
    def generate_key_from_spectrogram(
        self,
        mel_spectrogram: np.ndarray,
        pin: Optional[str] = None
    ) -> bytes:
        """
        Generate cryptographic key from spectrogram
        
        Args:
            mel_spectrogram: Mel-spectrogram feature matrix
            pin: Optional PIN to combine with audio (for user specificity)
            
        Returns:
            Generated key as bytes
        """
        # Get bit representation from spectrogram
        audio_bits = self.spectrogram_to_bits(mel_spectrogram)
        
        # Combine with PIN if provided
        if pin:
            pin_hash = hashlib.sha256(pin.encode()).digest()
            combined = audio_bits + pin_hash
        else:
            combined = audio_bits
        
        # Hash to get fixed-length key
        h = SHA256.new(combined)
        key = h.digest()[:self.key_length]
        
        return key
    
    def generate_key_from_audio_features(
        self,
        spectral_features: dict,
        pin: Optional[str] = None
    ) -> bytes:
        """
        Alternative method: generate key from spectral statistics
        
        Args:
            spectral_features: Dictionary of spectral features
            pin: Optional PIN
            
        Returns:
            Generated key as bytes
        """
        # Convert features to binary representation
        feature_bytes = b''
        
        for key, value in spectral_features.items():
            # Convert float to bytes
            feature_bytes += float(value).hex().encode()
        
        if pin:
            pin_hash = hashlib.sha256(pin.encode()).digest()
            feature_bytes += pin_hash
        
        # Generate key via hashing
        h = SHA256.new(feature_bytes)
        key = h.digest()[:self.key_length]
        
        return key
    
    def key_to_hex(self, key: bytes) -> str:
        """Convert key to hex string for display/storage"""
        return key.hex()
    
    def hex_to_key(self, hex_string: str) -> bytes:
        """Convert hex string back to key bytes"""
        return bytes.fromhex(hex_string)
