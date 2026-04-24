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
    next_action: str
    retry_recommended: bool
    agent_trace: List[Dict[str, str]]


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

    @staticmethod
    def _trace_step(stage: str, message: str, detail: Optional[str] = None) -> Dict[str, str]:
        step = {
            "stage": stage,
            "message": message,
            "time": datetime.now().isoformat(),
        }
        if detail:
            step["detail"] = detail
        return step

    @staticmethod
    def _feature_summary(features: Dict[str, float]) -> str:
        return (
            f"energy={features.get('energy', 0):.4f}, "
            f"rms={features.get('rms_energy', 0):.4f}, "
            f"centroid={features.get('spectral_centroid', 0):.4f}, "
            f"rolloff={features.get('spectral_rolloff', 0):.4f}, "
            f"zcr={features.get('zero_crossing_rate', 0):.4f}"
        )

    def _build_plan(self, analysis_result: AudioAnalysisResult, user_pin: Optional[str]) -> List[str]:
        features = analysis_result.features
        plan = [
            "Observe audio features and build a quality snapshot",
            "Score rule-based quality signals",
            "Consult the ML model if it is available",
            "Review whether the first pass is strong enough to accept",
        ]

        if features.get("energy", 0) <= 0:
            plan.append("Fallback early because the segment has no usable energy")
        elif features.get("zero_crossing_rate", 0) < 0.08:
            plan.append("Pay extra attention to complexity and segment diversity")

        if user_pin:
            plan.append("Bind the final key to the user PIN for stronger entropy")

        return plan

    def _review_decision(
        self,
        combined_score: float,
        risk_factors: List[str],
        ml_prediction: str,
        ml_confidence: float,
    ) -> Tuple[bool, str, List[str]]:
        reviewer_notes = []
        retry_recommended = False

        if combined_score < 0.5:
            retry_recommended = True
            reviewer_notes.append("Score is below the safe acceptance band.")
        elif combined_score < 0.7 and risk_factors:
            retry_recommended = True
            reviewer_notes.append("Borderline confidence plus risks suggests another segment should be tested.")
        else:
            reviewer_notes.append("The decision is strong enough to proceed.")

        if ml_prediction == "Error":
            reviewer_notes.append("ML step failed, so the agent fell back to expert rules.")
        elif ml_prediction not in {"Good", "Weak", "Unknown"}:
            reviewer_notes.append(f"ML prediction returned {ml_prediction} with confidence {ml_confidence:.2f}.")

        next_action = "retry_with_another_segment" if retry_recommended else "generate_key"
        return retry_recommended, next_action, reviewer_notes
    
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
        agent_trace = []

        features = analysis_result.features
        plan = self._build_plan(analysis_result, user_pin)

        agent_trace.append(self._trace_step("observe", "Captured audio feature snapshot.", self._feature_summary(features)))
        agent_trace.append(self._trace_step("plan", "Constructed evaluation plan.", " -> ".join(plan)))
        
        # Rule 1: Energy Distribution
        energy_score, energy_reason = self.rules_engine.check_energy_distribution(features)
        scores['energy'] = energy_score
        agent_trace.append(self._trace_step("rule", "Energy distribution scored.", f"score={energy_score:.2f}; {energy_reason}"))
        
        if energy_score < 0.5:
            risk_factors.append(f"Energy: {energy_reason}")
            recommendations.append("Try audio with more uniform energy distribution")
        
        # Rule 2: Spectral Diversity
        diversity_score, diversity_reason = self.rules_engine.check_spectral_diversity(features)
        scores['diversity'] = diversity_score
        agent_trace.append(self._trace_step("rule", "Spectral diversity scored.", f"score={diversity_score:.2f}; {diversity_reason}"))
        
        if diversity_score < 0.6:
            risk_factors.append(f"Diversity: {diversity_reason}")
            recommendations.append("Use audio with broader frequency content")
        
        # Rule 3: Zero Crossing Rate
        zcr_score, zcr_reason = self.rules_engine.check_zero_crossing_rate(features)
        scores['zcr'] = zcr_score
        agent_trace.append(self._trace_step("rule", "Complexity scored via zero-crossing rate.", f"score={zcr_score:.2f}; {zcr_reason}"))
        
        if zcr_score < 0.5:
            recommendations.append("Use audio with more complexity (speech or music)")
        
        # Combine rule-based scores
        rule_based_score = np.mean(list(scores.values()))
        agent_trace.append(self._trace_step("aggregate", "Aggregated rule-based score.", f"score={rule_based_score:.2f}"))
        
        # Get ML model prediction if available
        ml_prediction = "Unknown"
        ml_confidence = 0.5
        
        if self.ml_model is not None:
            try:
                ml_prediction, ml_confidence = self.ml_model.predict_key_quality(
                    analysis_result.spectrogram,
                    device='cpu'
                )
                agent_trace.append(self._trace_step("model", "ML model consulted.", f"prediction={ml_prediction}; confidence={ml_confidence:.2f}"))
            except Exception as e:
                print(f"ML model prediction failed: {e}")
                ml_prediction = "Error"
                ml_confidence = 0.0
                agent_trace.append(self._trace_step("model", "ML model failed; using rule fallback.", str(e)))
        else:
            agent_trace.append(self._trace_step("model", "No ML model loaded; using expert rules only."))
        
        # Decision logic: combine expert system and ML model
        # Expert system weight: 0.6, ML model weight: 0.4
        if ml_prediction == "Good":
            ml_numeric_score = 0.9
        elif ml_prediction == "Weak":
            ml_numeric_score = 0.35
        elif ml_prediction == "Error":
            ml_numeric_score = 0.4
        else:
            ml_numeric_score = 0.5
        combined_score = (rule_based_score * 0.6) + (ml_numeric_score * 0.4)
        agent_trace.append(self._trace_step("act", "Combined rule and model signals into a decision score.", f"score={combined_score:.2f}"))
        
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

        retry_recommended, next_action, reviewer_notes = self._review_decision(
            combined_score,
            risk_factors,
            ml_prediction,
            ml_confidence,
        )
        agent_trace.append(self._trace_step("review", "Performed a self-check on the decision.", " | ".join(reviewer_notes)))

        if retry_recommended and decision == "ACCEPT" and quality_level in {KeyQualityLevel.FAIR, KeyQualityLevel.WEAK}:
            recommendations.append("Agent review suggests testing another segment before finalizing.")
        
        # Additional recommendations based on PIN usage
        if user_pin:
            recommendations.append("✓ PIN + audio combination will further enhance security")
        else:
            recommendations.append("💡 Consider adding a PIN for additional security")
        
        if next_action == "retry_with_another_segment":
            recommendations.append("Agentic next action: retry with another segment and compare the outcome.")
        
        # Create evaluation report
        report = KeyEvaluationReport(
            quality_level=quality_level,
            confidence=combined_score,
            recommendations=recommendations,
            risk_factors=risk_factors,
            ml_model_prediction=ml_prediction,
            ml_model_confidence=ml_confidence,
            timestamp=timestamp,
            decision=decision,
            next_action=next_action,
            retry_recommended=retry_recommended,
            agent_trace=agent_trace,
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
            'architecture': 'Observe-Plan-Act-Review Agent',
            'rules': ['energy_distribution', 'spectral_diversity', 'zero_crossing_rate'],
            'agentic_loop': ['observe', 'plan', 'act', 'review'],
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
            'recommendation': best_report.recommendations[0] if best_report.recommendations else "Evaluation complete",
            'agent_trace': best_report.agent_trace,
            'next_action': best_report.next_action,
            'retry_recommended': best_report.retry_recommended,
        }
