"""
AudioKeyCNN Model
Convolutional Neural Network for audio key quality evaluation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple


class AudioKeyCNN(nn.Module):
    """
    CNN model for evaluating audio-derived key quality
    Input: Mel-spectrogram (1 x 128 x Time)
    Output: Key quality score (0-1) or binary classification
    """
    
    def __init__(self, num_classes: int = 2, dropout_rate: float = 0.3):
        """
        Initialize AudioKeyCNN model
        
        Args:
            num_classes: Number of output classes (2 for good/weak)
            dropout_rate: Dropout rate for regularization
        """
        super(AudioKeyCNN, self).__init__()
        self.num_classes = num_classes
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(4, 4), stride=(2, 2), padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.dropout1 = nn.Dropout(dropout_rate)
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=(4, 4), stride=(2, 2), padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.dropout2 = nn.Dropout(dropout_rate)
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), stride=(1, 1), padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.dropout3 = nn.Dropout(dropout_rate)
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Fully connected layers
        self.fc1 = nn.Linear(128, 64)
        self.fc_dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(64, num_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor of shape (batch_size, 1, height, width)
            
        Returns:
            Output logits or probabilities
        """
        # Conv block 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)
        x = self.dropout1(x)
        
        # Conv block 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)
        x = self.dropout2(x)
        
        # Conv block 3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.pool3(x)
        x = self.dropout3(x)
        
        # Global pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc_dropout(x)
        x = self.fc2(x)
        
        return x
    
    def predict_key_quality(self, mel_spectrogram: np.ndarray, device: str = 'cpu') -> Tuple[str, float]:
        """
        Predict key quality from mel-spectrogram
        
        Args:
            mel_spectrogram: Mel-spectrogram array
            device: Device to run on ('cpu' or 'cuda')
            
        Returns:
            Tuple of (quality_label, confidence)
        """
        self.eval()
        
        # Prepare input
        if len(mel_spectrogram.shape) == 2:
            # Add batch and channel dimensions
            mel_spectrogram = mel_spectrogram[np.newaxis, np.newaxis, :, :]
        
        # Convert to tensor
        x = torch.from_numpy(mel_spectrogram).float().to(device)
        
        # Forward pass
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
        
        # Get prediction
        pred_class = torch.argmax(logits, dim=1).item()
        confidence = probs[0, pred_class].item()
        
        label = "Good" if pred_class == 0 else "Weak"
        
        return label, confidence
    
    def get_model_info(self) -> dict:
        """Get model information"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'num_classes': self.num_classes,
            'model_name': 'AudioKeyCNN'
        }


class SimpleAudioKeyModel(nn.Module):
    """Simpler version of AudioKeyCNN for testing/quick training"""
    
    def __init__(self, num_classes: int = 2):
        super(SimpleAudioKeyModel, self).__init__()
        
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(32, num_classes)
    
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x
