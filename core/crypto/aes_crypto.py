"""
AES encryption/decryption module
Handles encryption and decryption using AES-256
"""

import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import json
from typing import Union


class AESCrypto:
    """Handles AES-256-CBC encryption and decryption"""
    
    def __init__(self):
        """Initialize AES crypto"""
        self.block_size = AES.block_size
    
    def encrypt(self, plaintext: Union[str, bytes], key: bytes) -> dict:
        """
        Encrypt plaintext using AES-256-CBC
        
        Args:
            plaintext: Text or bytes to encrypt
            key: Encryption key (32 bytes for AES-256)
            
        Returns:
            Dictionary with 'iv' and 'ciphertext' (both hex-encoded)
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Validate key length
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        
        # Generate random IV
        iv = get_random_bytes(self.block_size)
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Pad and encrypt
        padded_plaintext = pad(plaintext, self.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)
        
        return {
            'iv': iv.hex(),
            'ciphertext': ciphertext.hex()
        }
    
    def decrypt(self, ciphertext_dict: dict, key: bytes) -> str:
        """
        Decrypt ciphertext using AES-256-CBC
        
        Args:
            ciphertext_dict: Dictionary with 'iv' and 'ciphertext' (hex-encoded)
            key: Decryption key (32 bytes for AES-256)
            
        Returns:
            Decrypted plaintext as string
        """
        # Validate key length
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        
        # Convert from hex
        iv = bytes.fromhex(ciphertext_dict['iv'])
        ciphertext = bytes.fromhex(ciphertext_dict['ciphertext'])
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt and unpad
        padded_plaintext = cipher.decrypt(ciphertext)
        plaintext = unpad(padded_plaintext, self.block_size)
        
        return plaintext.decode('utf-8')
    
    def encrypt_file(self, input_path: str, output_path: str, key: bytes) -> dict:
        """
        Encrypt a file
        
        Args:
            input_path: Path to input file
            output_path: Path to output encrypted file
            key: Encryption key
            
        Returns:
            Dictionary with encryption metadata
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        
        # Read file
        with open(input_path, 'rb') as f:
            plaintext = f.read()
        
        # Generate IV
        iv = get_random_bytes(self.block_size)
        
        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_plaintext = pad(plaintext, self.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)
        
        # Write encrypted file
        with open(output_path, 'wb') as f:
            f.write(iv + ciphertext)
        
        return {
            'output_path': output_path,
            'file_size': len(plaintext),
            'encrypted_size': len(iv + ciphertext),
            'iv': iv.hex()
        }
    
    def decrypt_file(self, input_path: str, output_path: str, key: bytes) -> dict:
        """
        Decrypt a file
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to output decrypted file
            key: Decryption key
            
        Returns:
            Dictionary with decryption metadata
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        
        # Read encrypted file
        with open(input_path, 'rb') as f:
            data = f.read()
        
        # Extract IV and ciphertext
        iv = data[:self.block_size]
        ciphertext = data[self.block_size:]
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)
        plaintext = unpad(padded_plaintext, self.block_size)
        
        # Write decrypted file
        with open(output_path, 'wb') as f:
            f.write(plaintext)
        
        return {
            'output_path': output_path,
            'decrypted_size': len(plaintext)
        }
