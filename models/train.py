"""
Training script for AudioKeyCNN model
Trains the model on synthetic or real audio-based key quality labels
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.audkeycnn import AudioKeyCNN, SimpleAudioKeyModel
from core.audio_processor import AudioProcessor


class SyntheticAudioDataset(Dataset):
    """
    Synthetic dataset for training
    Generates random mel-spectrograms with labels based on statistical properties
    """
    
    def __init__(self, num_samples: int = 100, audio_duration: float = 3.0, sr: int = 22050):
        """
        Initialize dataset
        
        Args:
            num_samples: Number of samples to generate
            audio_duration: Duration of each audio in seconds
            sr: Sample rate
        """
        self.num_samples = num_samples
        self.sr = sr
        self.audio_processor = AudioProcessor(sr=sr)
        
        # Generate synthetic data
        self.spectrograms = []
        self.labels = []
        
        self._generate_samples()
    
    def _generate_samples(self):
        """Generate synthetic mel-spectrograms"""
        print("Generating synthetic audio data...")
        
        for i in range(self.num_samples):
            # Generate random audio
            if i < self.num_samples // 2:
                # "Good key" - complex, varied content
                audio = self._generate_good_audio()
                label = 0  # Good
            else:
                # "Weak key" - simple, repetitive content
                audio = self._generate_weak_audio()
                label = 1  # Weak
            
            # Extract spectrogram
            mel_spec = self.audio_processor.extract_mel_spectrogram(audio)
            
            # Normalize
            mel_spec = (mel_spec - mel_spec.mean()) / (mel_spec.std() + 1e-8)
            
            self.spectrograms.append(mel_spec)
            self.labels.append(label)
        
        print(f"✓ Generated {self.num_samples} samples")
    
    def _generate_good_audio(self) -> np.ndarray:
        """Generate "good key" audio - complex and varied"""
        length = int(3.0 * self.sr)  # 3 seconds
        
        # Mix of frequencies and randomness
        t = np.linspace(0, 3, length)
        rng = np.random.RandomState(42)
        
        # Multiple frequency components
        audio = (
            0.3 * np.sin(2 * np.pi * 440 * t) +  # 440 Hz
            0.2 * np.sin(2 * np.pi * 880 * t) +  # 880 Hz
            0.2 * np.sin(2 * np.pi * 220 * t) +  # 220 Hz
            0.2 * rng.randn(length)  # White noise
        )
        
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        return audio
    
    def _generate_weak_audio(self) -> np.ndarray:
        """Generate "weak key" audio - simple and repetitive"""
        length = int(3.0 * self.sr)  # 3 seconds
        
        # Single frequency or very simple content
        t = np.linspace(0, 3, length)
        audio = 0.8 * np.sin(2 * np.pi * 1000 * t)  # Single tone
        
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        return audio
    
    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        spectrogram = self.spectrograms[idx]
        label = self.labels[idx]
        
        # Add channel dimension
        spectrogram = np.expand_dims(spectrogram, axis=0)
        spectrogram = torch.from_numpy(spectrogram).float()
        
        return spectrogram, label


def train_model(model, train_loader, val_loader, num_epochs: int = 10, learning_rate: float = 0.001):
    """
    Train the model
    
    Args:
        model: Model to train
        train_loader: Training data loader
        val_loader: Validation data loader
        num_epochs: Number of epochs
        learning_rate: Learning rate
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}\n")
    
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    best_val_acc = 0.0
    patience = 5
    patience_counter = 0
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (spectrograms, labels) in enumerate(train_loader):
            spectrograms = spectrograms.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(spectrograms)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for spectrograms, labels in val_loader:
                spectrograms = spectrograms.to(device)
                labels = labels.to(device)
                
                outputs = model(spectrograms)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        # Print statistics
        train_acc = 100 * train_correct / train_total
        val_acc = 100 * val_correct / val_total
        
        print(f"Epoch [{epoch+1}/{num_epochs}]")
        print(f"  Train Loss: {train_loss:.4f}, Accuracy: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f}, Accuracy: {val_acc:.2f}%\n")
        
        # Early stopping
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            
            # Save best model
            torch.save(model.state_dict(), project_root / 'models' / 'audkeycnn_pretrained.pt')
            print(f"✓ Model saved (Best Val Acc: {best_val_acc:.2f}%)\n")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    print(f"\n✓ Training complete! Best validation accuracy: {best_val_acc:.2f}%")


def main():
    print(f"{'='*60}")
    print("AudioKeyCNN Model Training")
    print(f"{'='*60}\n")
    
    # Create dataset
    print("Creating synthetic dataset...")
    train_dataset = SyntheticAudioDataset(num_samples=200)
    val_dataset = SyntheticAudioDataset(num_samples=50)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    
    # Create model
    print("\nInitializing AudioKeyCNN model...")
    model = AudioKeyCNN(num_classes=2, dropout_rate=0.3)
    
    print(f"Model info:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Train model
    print("\n" + f"{'='*60}")
    print("Starting training...")
    print(f"{'='*60}\n")
    
    train_model(model, train_loader, val_loader, num_epochs=15, learning_rate=0.001)
    
    print("\n✓ Training pipeline complete!")
    print(f"✓ Model saved to: {project_root / 'models' / 'audkeycnn_pretrained.pt'}")


if __name__ == '__main__':
    main()
