"""
AudioKey CLI Application
Command-line interface for audio-based key generation and encryption
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.audio_processor import AudioProcessor
from core.keygen import KeyGenerator
from core.crypto.aes_crypto import AESCrypto
from agent.key_quality_agent import (
    AudioKeyAgent,
    AudioAnalysisResult,
    KeyEvaluationWorkflow
)
from models.audkeycnn import AudioKeyCNN
import torch
import os


class AudioKeyCLI:
    """Command-line interface for AudioKey"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.key_generator = KeyGenerator(key_length=32)  # 256-bit key
        self.crypto = AESCrypto()
        
        # Try to load pre-trained model
        self.model = None
        self._load_model()
        
        # Initialize agent
        self.agent = AudioKeyAgent(ml_model=self.model)
        self.workflow = KeyEvaluationWorkflow(self.agent)
    
    def _load_model(self):
        """Load pre-trained model if available"""
        model_path = project_root / 'models' / 'audkeycnn_pretrained.pt'
        
        if model_path.exists():
            try:
                self.model = AudioKeyCNN(num_classes=2)
                self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
                self.model.eval()
                print(f"✓ Loaded pre-trained model from {model_path}")
            except Exception as e:
                print(f"⚠ Could not load model: {e}")
                self.model = None
        else:
            print("ℹ No pre-trained model found (this is optional)")
    
    def generate_key_from_audio(
        self,
        audio_path: str,
        pin: str = None,
        evaluate: bool = True,
        save_processed: bool = False,
        processed_dir: str = 'data/processed'
    ):
        """
        Generate encryption key from audio file
        
        Args:
            audio_path: Path to audio file
            pin: Optional PIN for additional security
            evaluate: Whether to run quality evaluation first
        """
        print(f"\n{'='*60}")
        print(f"AudioKey - Key Generation")
        print(f"{'='*60}\n")
        
        # Check file exists
        if not os.path.exists(audio_path):
            print(f"✗ Error: Audio file not found: {audio_path}")
            return None
        
        print(f"📁 Audio File: {audio_path}")
        
        # Process audio
        print("🔄 Processing audio...")
        result_dict = self.audio_processor.process_audio_file(audio_path)
        
        print(f"✓ Extracted {len(result_dict['segments'])} segments")
        print(f"✓ Sample rate: {result_dict['sample_rate']} Hz")
        
        if evaluate:
            print("\n🤖 Running AI Quality Evaluation...")
            
            # Create analysis results for each segment
            analysis_results = []
            for i, (segment, spec, features) in enumerate(zip(
                result_dict['segments'],
                result_dict['spectrograms'],
                result_dict['features']
            )):
                analysis_results.append(
                    AudioAnalysisResult(
                        spectrogram=spec,
                        features=features,
                        timestamp="",
                        duration=len(segment) / result_dict['sample_rate'],
                        segment_id=f"seg_{i}"
                    )
                )
            
            # Run workflow
            pipeline_result = self.workflow.run_evaluation_pipeline(analysis_results, pin)
            
            print(f"\n📊 Evaluation Results:")
            print(f"   Accepted segments: {pipeline_result['accepted_segments']}/{pipeline_result['total_segments']}")
            
            best_report = pipeline_result['best_report']
            print(f"   Best segment quality: {best_report.quality_level.name}")
            print(f"   Confidence: {best_report.confidence:.2%}")
            print(f"   Decision: {best_report.decision}")
            print(f"   Next action: {pipeline_result['next_action']}")
            print(f"   Retry recommended: {pipeline_result['retry_recommended']}")
            
            if best_report.risk_factors:
                print(f"\n   ⚠ Risk Factors:")
                for risk in best_report.risk_factors:
                    print(f"      - {risk}")
            
            if best_report.recommendations:
                print(f"\n   💡 Recommendations:")
                for rec in best_report.recommendations:
                    print(f"      - {rec}")

            if pipeline_result.get('agent_trace'):
                print(f"\n   🔎 Agent Trace:")
                for step in pipeline_result['agent_trace']:
                    detail = step.get('detail')
                    line = f"      - [{step.get('stage')}] {step.get('message')}"
                    if detail:
                        line += f" :: {detail}"
                    print(line)
            
            # Use best segment
            best_idx = pipeline_result['best_segment_index']
            best_segment = result_dict['segments'][best_idx]
            best_spec = result_dict['spectrograms'][best_idx]
        else:
            # Use first segment
            best_idx = 0
            best_segment = result_dict['segments'][0]
            best_spec = result_dict['spectrograms'][0]

        if save_processed:
            output_path = Path(processed_dir) / f"{Path(audio_path).stem}_processed_seg{best_idx}.wav"
            saved_path = self.audio_processor.save_audio(
                best_segment,
                str(output_path),
                sr=result_dict['sample_rate']
            )
            print(f"✓ Processed segment saved")
            print(f"   Output wav: {saved_path}")
        
        # Generate key
        print(f"\n🔑 Generating cryptographic key...")
        key = self.key_generator.generate_key_from_spectrogram(best_spec, pin)
        key_hex = self.key_generator.key_to_hex(key)
        
        print(f"✓ Generated 256-bit AES key")
        print(f"   Key (hex): {key_hex}")
        
        return key, key_hex
    
    def encrypt_text(self, text: str, key: bytes):
        """Encrypt text with key"""
        print(f"\n📝 Encrypting text...")
        encrypted = self.crypto.encrypt(text, key)
        
        print(f"✓ Text encrypted successfully")
        print(f"   IV: {encrypted['iv']}")
        print(f"   Ciphertext: {encrypted['ciphertext'][:64]}...")
        
        return encrypted
    
    def decrypt_text(self, encrypted_dict: dict, key: bytes):
        """Decrypt text with key"""
        print(f"\n🔓 Decrypting text...")
        plaintext = self.crypto.decrypt(encrypted_dict, key)
        
        print(f"✓ Text decrypted successfully")
        print(f"   Plaintext: {plaintext}")
        
        return plaintext
    
    def encrypt_file(self, input_file: str, key: bytes):
        """Encrypt a file"""
        output_file = input_file + ".enc"
        
        print(f"\n📁 Encrypting file...")
        print(f"   Input: {input_file}")
        
        result = self.crypto.encrypt_file(input_file, output_file, key)
        
        print(f"✓ File encrypted")
        print(f"   Output: {output_file}")
        print(f"   Size: {result['file_size']} → {result['encrypted_size']} bytes")
        
        return output_file
    
    def decrypt_file(self, input_file: str, key: bytes):
        """Decrypt a file"""
        output_file = input_file.replace('.enc', '.dec')
        
        print(f"\n🔓 Decrypting file...")
        print(f"   Input: {input_file}")
        
        result = self.crypto.decrypt_file(input_file, output_file, key)
        
        print(f"✓ File decrypted")
        print(f"   Output: {output_file}")
        print(f"   Size: {result['decrypted_size']} bytes")
        
        return output_file
    
    def show_agent_info(self):
        """Display agent information"""
        info = self.agent.get_agent_info()
        
        print(f"\n{'='*60}")
        print(f"🤖 AudioKey Quality Evaluation Agent")
        print(f"{'='*60}\n")
        
        for key, value in info.items():
            print(f"{key:.<40} {value}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="AudioKey - Audio-based Encryption Key Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate key from audio and evaluate quality
  python cli.py generate-key audio.wav --evaluate
  
  # Generate key with PIN
  python cli.py generate-key audio.wav --pin "mypin123"
  
  # Encrypt text
  python cli.py encrypt-text "Hello World" key_hex --key-hex
  
  # Show agent info
  python cli.py agent-info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate key command
    gen_parser = subparsers.add_parser('generate-key', help='Generate key from audio')
    gen_parser.add_argument('audio_file', help='Path to audio file')
    gen_parser.add_argument('--pin', help='Optional PIN for security')
    gen_parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Run quality evaluation (enabled by default; kept for compatibility)'
    )
    gen_parser.add_argument('--no-evaluate', action='store_true', help='Skip quality evaluation')
    gen_parser.add_argument('--save-processed', action='store_true', help='Save selected processed segment as wav')
    gen_parser.add_argument('--processed-dir', default='data/processed', help='Directory for saved processed wav')
    
    # Encrypt text command
    enc_parser = subparsers.add_parser('encrypt-text', help='Encrypt text')
    enc_parser.add_argument('text', help='Text to encrypt')
    enc_parser.add_argument('key', help='Encryption key (hex format)')
    
    # Decrypt text command
    dec_parser = subparsers.add_parser('decrypt-text', help='Decrypt text')
    dec_parser.add_argument('ciphertext', help='Ciphertext (hex format)')
    dec_parser.add_argument('iv', help='IV (hex format)')
    dec_parser.add_argument('key', help='Decryption key (hex format)')
    
    # Show agent info
    subparsers.add_parser('agent-info', help='Show agent information')
    
    args = parser.parse_args()
    
    cli = AudioKeyCLI()
    
    if args.command == 'generate-key':
        cli.generate_key_from_audio(
            args.audio_file,
            pin=args.pin,
            evaluate=not args.no_evaluate,
            save_processed=args.save_processed,
            processed_dir=args.processed_dir
        )
    
    elif args.command == 'encrypt-text':
        key = bytes.fromhex(args.key)
        cli.encrypt_text(args.text, key)
    
    elif args.command == 'decrypt-text':
        key = bytes.fromhex(args.key)
        encrypted_dict = {'iv': args.iv, 'ciphertext': args.ciphertext}
        cli.decrypt_text(encrypted_dict, key)
    
    elif args.command == 'agent-info':
        cli.show_agent_info()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
