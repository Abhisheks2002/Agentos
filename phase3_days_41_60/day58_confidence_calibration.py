"""
Day 58: Confidence Calibration
==============================
Calibrating model confidence with actual accuracy.

Key Concepts:
- Confidence scoring
- Calibration curves
- Temperature scaling
- Platt scaling
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random
import math


@dataclass
class Prediction:
    """A prediction with confidence"""
    id: str
    question: str
    predicted_answer: str
    true_answer: str = None
    confidence: float = 0.5
    is_correct: bool = False


@dataclass
class CalibrationResult:
    """Result of calibration"""
    accuracy: float
    average_confidence: float
    calibration_error: float  # ECE
    predictions: List[Prediction]


class ConfidenceEstimator:
    """
    Confidence Estimator
    ====================

    Estimate confidence for model predictions.
    """

    def __init__(self, model=None):
        self.model = model

    def estimate_from_logits(self, logits: List[float]) -> float:
        """Estimate confidence from logits"""
        if not logits:
            return 0.5

        # Softmax
        exp_logits = [math.exp(l) for l in logits]
        sum_exp = sum(exp_logits)
        probs = [e / sum_exp for e in exp_logits]

        # Confidence is max probability
        return max(probs)

    def estimate_from_logprobs(self, logprobs: List[float]) -> float:
        """Estimate confidence from log probabilities"""
        if not logprobs:
            return 0.5

        # Convert to probabilities
        probs = [math.exp(lp) for lp in logprobs]
        return max(probs)

    def estimate_semantic(self, answer: str, alternatives: List[str]) -> float:
        """Estimate confidence from semantic similarity"""
        if not alternatives:
            return 0.5

        # Simple word overlap
        answer_words = set(answer.lower().split())

        similarities = []
        for alt in alternatives:
            alt_words = set(alt.lower().split())
            if answer_words and alt_words:
                overlap = len(answer_words & alt_words) / len(answer_words | alt_words)
                similarities.append(overlap)

        return sum(similarities) / len(similarities) if similarities else 0.5


class TemperatureScaler:
    """
    Temperature Scaling
    ==================

    Calibrate confidence using temperature scaling.
    """

    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature

    def calibrate(self, logits: List[float]) -> List[float]:
        """Apply temperature scaling to logits"""
        if self.temperature == 1.0:
            return logits

        return [l / self.temperature for l in logits]

    def get_confidence(self, logits: List[float]) -> float:
        """Get calibrated confidence"""
        calibrated = self.calibrate(logits)
        ce = ConfidenceEstimator()
        return ce.estimate_from_logits(calibrated)

    def find_optimal_temperature(
        self,
        predictions: List[Prediction],
        search_range: Tuple[float, float] = (0.5, 3.0),
        num_steps: int = 20
    ) -> float:
        """Find optimal temperature using NLL"""
        best_temp = 1.0
        best_nll = float('inf')

        temps = [
            search_range[0] + (search_range[1] - search_range[0]) * i / num_steps
            for i in range(num_steps + 1)
        ]

        for temp in temps:
            scaler = TemperatureScaler(temperature=temp)
            nll = 0

            for pred in predictions:
                # Get logits (use confidence as proxy)
                logit = math.log(pred.confidence + 1e-10)
                calibrated_logit = logit / temp

                # Calculate NLL
                if pred.is_correct:
                    nll -= calibrated_logit

            if nll < best_nll:
                best_nll = nll
                best_temp = temp

        self.temperature = best_temp
        return best_temp


class PlattScaler:
    """
    Platt Scaling
    =============

    Calibrate confidence using logistic regression.
    """

    def __init__(self):
        self.a = 1.0  # Slope
        self.b = 0.0  # Intercept

    def fit(self, predictions: List[Prediction]):
        """Fit Platt scaling parameters"""
        # Extract features (logits) and labels
        features = [math.log(p.confidence + 1e-10) for p in predictions]
        labels = [1 if p.is_correct else 0 for p in predictions]

        if not features:
            return

        # Simple Platt scaling (simplified)
        # In practice, use sklearn's LogisticRegression
        correct_rate = sum(labels) / len(labels)

        if correct_rate > 0:
            self.a = 1.0 / max(correct_rate, 0.1)
            self.b = -math.log(max(correct_rate / (1 - correct_rate + 1e-10), 0.1))

    def calibrate(self, confidence: float) -> float:
        """Apply Platt scaling"""
        logit = math.log(confidence + 1e-10)
        calibrated_logit = self.a * logit + self.b
        return 1 / (1 + math.exp(-calibrated_logit))


class CalibrationEvaluator:
    """
    Calibration Evaluator
    ======================

    Evaluate calibration quality.
    """

    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins

    def calculate_ece(
        self,
        predictions: List[Prediction]
    ) -> float:
        """Calculate Expected Calibration Error (ECE)"""
        if not predictions:
            return 0.0

        # Bin predictions by confidence
        bin_boundaries = [
            i / self.num_bins for i in range(self.num_bins + 1)
        ]
        bins = [[] for _ in range(self.num_bins)]

        for pred in predictions:
            bin_idx = min(
                int(pred.confidence * self.num_bins),
                self.num_bins - 1
            )
            bins[bin_idx].append(pred)

        # Calculate ECE
        ece = 0
        total = len(predictions)

        for bin_preds in bins:
            if not bin_preds:
                continue

            bin_accuracy = sum(1 for p in bin_preds if p.is_correct) / len(bin_preds)
            bin_confidence = sum(p.confidence for p in bin_preds) / len(bin_preds)

            ece += len(bin_preds) / total * abs(bin_accuracy - bin_confidence)

        return ece

    def calculate_mce(
        self,
        predictions: List[Prediction]
    ) -> float:
        """Calculate Maximum Calibration Error"""
        if not predictions:
            return 0.0

        bin_boundaries = [
            i / self.num_bins for i in range(self.num_bins + 1)
        ]
        bins = [[] for _ in range(self.num_bins)]

        for pred in predictions:
            bin_idx = min(
                int(pred.confidence * self.num_bins),
                self.num_bins - 1
            )
            bins[bin_idx].append(pred)

        max_error = 0

        for bin_preds in bins:
            if not bin_preds:
                continue

            bin_accuracy = sum(1 for p in bin_preds if p.is_correct) / len(bin_preds)
            bin_confidence = sum(p.confidence for p in bin_preds) / len(bin_preds)

            error = abs(bin_accuracy - bin_confidence)
            max_error = max(max_error, error)

        return max_error

    def get_calibration_curve(
        self,
        predictions: List[Prediction]
    ) -> Dict[str, List[float]]:
        """Get calibration curve data"""
        bin_boundaries = [
            i / self.num_bins for i in range(self.num_bins + 1)
        ]
        bins = [[] for _ in range(self.num_bins)]

        for pred in predictions:
            bin_idx = min(
                int(pred.confidence * self.num_bins),
                self.num_bins - 1
            )
            bins[bin_idx].append(pred)

        accuracies = []
        confidences = []
        counts = []

        for i, bin_preds in enumerate(bins):
            if not bin_preds:
                accuracies.append(0)
                confidences.append((bin_boundaries[i] + bin_boundaries[i+1]) / 2)
                counts.append(0)
            else:
                acc = sum(1 for p in bin_preds if p.is_correct) / len(bin_preds)
                conf = sum(p.confidence for p in bin_preds) / len(bin_preds)
                accuracies.append(acc)
                confidences.append(conf)
                counts.append(len(bin_preds))

        return {
            "accuracies": accuracies,
            "confidences": confidences,
            "counts": counts
        }


class CalibrationEngine:
    """
    Calibration Engine
    ===================

    Full calibration system.
    """

    def __init__(self):
        self.temp_scaler = TemperatureScaler()
        self.platt_scaler = PlattScaler()
        self.evaluator = CalibrationEvaluator()

    def add_prediction(
        self,
        question: str,
        answer: str,
        confidence: float,
        true_answer: str = None
    ) -> Prediction:
        """Add a prediction"""
        pred = Prediction(
            id=f"pred_{random.randint(1000, 9999)}",
            question=question,
            predicted_answer=answer,
            true_answer=true_answer,
            confidence=confidence,
            is_correct=(answer == true_answer) if true_answer else None
        )
        return pred

    def calibrate(
        self,
        predictions: List[Prediction],
        method: str = "temperature"
    ) -> CalibrationResult:
        """Calibrate predictions"""
        # Fit calibrator
        if method == "temperature":
            self.temp_scaler.find_optimal_temperature(predictions)
            for pred in predictions:
                pred.confidence = self.temp_scaler.get_confidence(
                    [math.log(pred.confidence + 1e-10)]
                )
        elif method == "platt":
            self.platt_scaler.fit(predictions)
            for pred in predictions:
                pred.confidence = self.platt_scaler.calibrate(pred.confidence)

        # Calculate metrics
        accuracy = sum(1 for p in predictions if p.is_correct) / len(predictions) if predictions else 0
        avg_conf = sum(p.confidence for p in predictions) / len(predictions) if predictions else 0
        ece = self.evaluator.calculate_ece(predictions)

        return CalibrationResult(
            accuracy=accuracy,
            average_confidence=avg_conf,
            calibration_error=ece,
            predictions=predictions
        )


# Demo function
def demo():
    """Demonstrate Confidence Calibration"""
    print("=" * 60)
    print("  Confidence Calibration Demo")
    print("=" * 60)

    # Create predictions
    predictions = []

    # Test predictions with varying confidence
    test_cases = [
        ("What is 2+2?", "4", "4", 0.95),
        ("What is the capital of France?", "Paris", "Paris", 0.92),
        ("What is 10*10?", "100", "100", 0.90),
        ("Explain quantum physics", "Complex", "Complex", 0.65),
        ("What is 1+1?", "3", "2", 0.55),  # Wrong high confidence
    ]

    engine = CalibrationEngine()

    for question, answer, true_answer, confidence in test_cases:
        pred = engine.add_prediction(question, answer, confidence, true_answer)
        predictions.append(pred)

    print("\n1. Original Predictions:")
    for p in predictions:
        correct = "✓" if p.is_correct else "✗"
        print(f"  {correct} Conf: {p.confidence:.2f} | Answer: {p.predicted_answer}")

    # Evaluate before calibration
    evaluator = CalibrationEvaluator()
    ece_before = evaluator.calculate_ece(predictions)

    print(f"\n2. Before Calibration:")
    print(f"  ECE: {ece_before:.3f}")

    # Calibrate
    result = engine.calibrate(predictions, method="temperature")

    print(f"\n3. After Calibration (Temperature):")
    print(f"  Accuracy: {result.accuracy:.2f}")
    print(f"  Avg Confidence: {result.average_confidence:.2f}")
    print(f"  ECE: {result.calibration_error:.3f}")

    print("\n4. Calibrated Predictions:")
    for p in result.predictions:
        print(f"  Conf: {p.confidence:.2f} | Answer: {p.predicted_answer}")

    # Calibration curve
    print("\n5. Calibration Curve:")
    curve = evaluator.get_calibration_curve(predictions)

    for i in range(len(curve["confidences"])):
        print(f"  Conf: {curve['confidences'][i]:.2f} | Acc: {curve['accuracies'][i]:.2f} | N: {curve['counts'][i]}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()