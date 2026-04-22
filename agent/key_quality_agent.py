"""
Agentic AI System for AudioKey
Uses an agent-based architecture for key evaluation and recommendation
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime


class KeyQualityLevel(Enum):
    """Enumeration for key quality levels"""
    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    WEAK = 2
    POOR = 1


@dataclass
class AudioAnalysisResult:
    """Result of audio analysis"""
    spectrogram: np.ndarray
    features: Dict[str, float]
    timestamp: str
    duration: float
    segment_id: str


@dataclass
class KeyEvaluationReport:
    """Report from key evaluation"""
    quality_level: KeyQualityLevel
    confidence: float
    recommendations: List[str]
    risk_factors: List[str]
    ml_model_prediction: str
    ml_model_confidence: float
    timestamp: str
    decision: str  # "ACCEPT" or "REJECT"


class KeyQualityRules:
    """
    Expert system rules for evaluating key quality
    Based on spectral characteristics and randomness metrics
    """
    
    @staticmethod
    def check_energy_distribution(features: Dict[str, float]) -> Tuple[float, str]:
        """
        Check energy distribution across frequency spectrum
        Good keys should have relatively uniform energy
        
        Returns: (score, reason)
        """
        rms_energy = features.get('rms_energy', 0)
        energy = features.get('energy', 0)
        
        if energy == 0:
            return 0.0, "No audio energy detected"
        
        # Ratio should be close to 1 for random-like content
        energy_ratio = rms_energy / (energy + 1e-8)
        
        if 0.7 <= energy_ratio <= 1.0:
            return 1.0, "Good energy distribution"
        elif 0.5 <= energy_ratio < 0.7:
            return 0.7, "Acceptable energy distribution"
        else:
            return 0.4, "Poor energy distribution - concentrated energy"
    
    @staticmethod
    def check_spectral_diversity(features: Dict[str, float]) -> Tuple[float, str]:
        """
        Check spectral diversity (good randomness indicator)
        Spectral centroid and rolloff should be in reasonable ranges
        """
        centroid = features.get('spectral_centroid', 0)
        rolloff = features.get('spectral_rolloff', 0)
        
        # Assuming normalized features (0-1 or 0-0.5)
        diversity_score = min(1.0, (centroid / 5000 + rolloff / 10000) / 2) if centroid > 0 else 0.5
        
        if diversity_score > 0.7:
            return 0.9, "Excellent spectral diversity"
        elif diversity_score > 0.5:
            return 0.7, "Good spectral diversity"
        else:
            return 0.5, "Limited spectral diversity"
    
    @staticmethod
    def check_zero_crossing_rate(features: Dict[str, float]) -> Tuple[float, str]:
        """
        Zero crossing rate is indicator of complexity
        Higher ZCR suggests more varied content
        """
        zcr = features.get('zero_crossing_rate', 0)
        
        if zcr > 0.3:
            return 1.0, "Excellent zero-crossing rate (high complexity)"
        elif zcr > 0.15:
            return 0.8, "Good zero-crossing rate"
        elif zcr > 0.05:
            return 0.5, "Moderate zero-crossing rate"
        else:
            return 0.2, "Low zero-crossing rate (low complexity)"


class AudioKeyAgent:
    """
    Agentic system for evaluating audio-derived keys
    Combines expert system rules with ML model predictions
    """
    
    def __init__(self, ml_model=None):
        """
        Initialize the agent
        
        Args:
            ml_model: Trained ML model for predictions (optional)
        """
        self.ml_model = ml_model
        self.evaluation_history: List[KeyEvaluationReport] = []
        self.rules_engine = KeyQualityRules()
        self.agent_name = "AudioKeyQualityAgent"
    
    def evaluate_audio_segment(
        self,
        analysis_result: AudioAnalysisResult,
        user_pin: Optional[str] = None
    ) -> KeyEvaluationReport:
        """
        Comprehensive evaluation of an audio segment for key quality
        
        This is the main agent decision-making logic
        
        Args:
            analysis_result: Audio analysis result
            user_pin: Optional PIN for context
            
        Returns:
            KeyEvaluationReport with decision
        """
        timestamp = datetime.now().isoformat()
        recommendations = []
        risk_factors = []
        scores = {}
        
        # Apply expert system rules
        features = analysis_result.features
        
        # Rule 1: Energy Distribution
        energy_score, energy_reason = self.rules_engine.check_energy_distribution(features)
        scores['energy'] = energy_score
        
        if energy_score < 0.5:
            risk_factors.append(f"Energy: {energy_reason}")
            recommendations.append("Try audio with more uniform energy distribution")
        
        # Rule 2: Spectral Diversity
        diversity_score, diversity_reason = self.rules_engine.check_spectral_diversity(features)
        scores['diversity'] = diversity_score
        
        if diversity_score < 0.6:
            risk_factors.append(f"Diversity: {diversity_reason}")
            recommendations.append("Use audio with broader frequency content")
        
        # Rule 3: Zero Crossing Rate
        zcr_score, zcr_reason = self.rules_engine.check_zero_crossing_rate(features)
        scores['zcr'] = zcr_score
        
        if zcr_score < 0.5:
            recommendations.append("Use audio with more complexity (speech or music)")
        
        # Combine rule-based scores
        rule_based_score = np.mean(list(scores.values()))
        
        # Get ML model prediction if available
        ml_prediction = "Unknown"
        ml_confidence = 0.5
        
        if self.ml_model is not None:
            try:
                ml_prediction, ml_confidence = self.ml_model.predict_key_quality(
                    analysis_result.spectrogram,
                    device='cpu'
                )
            except Exception as e:
                print(f"ML model prediction failed: {e}")
                ml_prediction = "Error"
                ml_confidence = 0.0
        
        # Decision logic: combine expert system and ML model
        # Expert system weight: 0.6, ML model weight: 0.4
        ml_numeric_score = 0.9 if ml_prediction == "Good" else 0.5
        combined_score = (rule_based_score * 0.6) + (ml_numeric_score * 0.4)
        
        # Determine quality level and decision
        if combined_score >= 0.8:
            quality_level = KeyQualityLevel.EXCELLENT
            decision = "ACCEPT"
            recommendations.append("✓ This audio segment is excellent for key generation!")
        elif combined_score >= 0.65:
            quality_level = KeyQualityLevel.GOOD
            decision = "ACCEPT"
            recommendations.append("✓ This audio segment is suitable for key generation")
        elif combined_score >= 0.50:
            quality_level = KeyQualityLevel.FAIR
            decision = "ACCEPT"
            recommendations.append("⚠ This segment is acceptable but could be improved")
        elif combined_score >= 0.35:
            quality_level = KeyQualityLevel.WEAK
            decision = "REJECT"
            risk_factors.append("Combined quality score is below acceptable threshold")
            recommendations.append("Try a different audio segment with higher diversity")
        else:
            quality_level = KeyQualityLevel.POOR
            decision = "REJECT"
            risk_factors.append("Critical: Very low quality score")
            recommendations.append("Please select a different audio file (music, speech, or varied noise)")
        
        # Additional recommendations based on PIN usage
        if user_pin:
            recommendations.append("✓ PIN + audio combination will further enhance security")
        else:
            recommendations.append("💡 Consider adding a PIN for additional security")
        
        # Create evaluation report
        report = KeyEvaluationReport(
            quality_level=quality_level,
            confidence=combined_score,
            recommendations=recommendations,
            risk_factors=risk_factors,
            ml_model_prediction=ml_prediction,
            ml_model_confidence=ml_confidence,
            timestamp=timestamp,
            decision=decision
        )
        
        # Store in history
        self.evaluation_history.append(report)
        
        return report
    
    def batch_evaluate(
        self,
        analysis_results: List[AudioAnalysisResult]
    ) -> List[KeyEvaluationReport]:
        """
        Evaluate multiple audio segments
        
        Args:
            analysis_results: List of audio analysis results
            
        Returns:
            List of evaluation reports
        """
        reports = []
        for result in analysis_results:
            report = self.evaluate_audio_segment(result)
            reports.append(report)
        
        return reports
    
    def get_best_segment(
        self,
        analysis_results: List[AudioAnalysisResult]
    ) -> Tuple[int, KeyEvaluationReport]:
        """
        Find the best audio segment from a list
        
        Args:
            analysis_results: List of audio analysis results
            
        Returns:
            Tuple of (best_segment_index, best_report)
        """
        reports = self.batch_evaluate(analysis_results)
        
        # Sort by confidence score
        best_idx = max(range(len(reports)), key=lambda i: reports[i].confidence)
        
        return best_idx, reports[best_idx]
    
    def get_agent_info(self) -> Dict:
        """Get information about the agent"""
        return {
            'agent_name': self.agent_name,
            'total_evaluations': len(self.evaluation_history),
            'has_ml_model': self.ml_model is not None,
            'architecture': 'Expert System + ML Hybrid',
            'rules': ['energy_distribution', 'spectral_diversity', 'zero_crossing_rate']
        }


class KeyEvaluationWorkflow:
    """Orchestrates the complete key evaluation workflow"""
    
    def __init__(self, agent: AudioKeyAgent):
        """
        Initialize workflow
        
        Args:
            agent: AudioKeyAgent instance
        """
        self.agent = agent
    
    def run_evaluation_pipeline(
        self,
        analysis_results: List[AudioAnalysisResult],
        user_pin: Optional[str] = None
    ) -> Dict:
        """
        Run complete evaluation pipeline
        
        Args:
            analysis_results: List of audio analysis results
            user_pin: Optional user PIN
            
        Returns:
            Dictionary with pipeline results
        """
        reports = []
        
        for result in analysis_results:
            report = self.agent.evaluate_audio_segment(result, user_pin)
            reports.append(report)
        
        # Find best segment
        best_idx = max(range(len(reports)), key=lambda i: reports[i].confidence)
        best_report = reports[best_idx]
        
        # Summary
        accepted_count = sum(1 for r in reports if r.decision == "ACCEPT")
        total_count = len(reports)
        
        return {
            'all_reports': reports,
            'best_segment_index': best_idx,
            'best_report': best_report,
            'accepted_segments': accepted_count,
            'total_segments': total_count,
            'recommendation': best_report.recommendations[0] if best_report.recommendations else "Evaluation complete"
        }
