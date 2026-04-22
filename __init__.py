"""
AudioKey - Main initialization file
"""

__version__ = "1.0.0"
__author__ = "AudioKey Team"
__description__ = "Security-Based AI System for Audio-Derived Encryption Keys"

from core import AudioProcessor, KeyGenerator, AESCrypto
from agent import AudioKeyAgent, KeyEvaluationWorkflow
from models import AudioKeyCNN

__all__ = [
    'AudioProcessor',
    'KeyGenerator',
    'AESCrypto',
    'AudioKeyAgent',
    'KeyEvaluationWorkflow',
    'AudioKeyCNN'
]
