"""
Day 57: Active-Prompt
=====================
Dynamic prompting based on uncertainty estimation.

Key Concepts:
- Estimate uncertainty
- Select uncertain examples for prompting
- Iterative refinement
- Difficulty-based example selection
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random
import uuid


@dataclass
class ActivePromptExample:
    """An example for active prompting"""
    id: str
    question: str
    answer: str
    uncertainty: float = 0.0
    difficulty: float = 0.0
    annotated: bool = False
    annotations: Dict[str, Any] = field(default_factory=dict)


class UncertaintyEstimator:
    """
    Uncertainty Estimator
    ======================

    Estimates uncertainty for model predictions.
    """

    def __init__(
        self,
        model: Callable[[str], Tuple[str, float]] = None,
        num_samples: int = 5
    ):
        self.model = model or self._default_model
        self.num_samples = num_samples

    def _default_model(self, prompt: str) -> Tuple[str, float]:
        """Default model (simulated)"""
        return "Answer", random.uniform(0.5, 1.0)

    def estimate_entropy(self, prompt: str) -> float:
        """Estimate uncertainty using entropy"""
        # Sample multiple responses
        responses = []
        for _ in range(self.num_samples):
            answer, _ = self.model(prompt)
            responses.append(answer)

        # Calculate entropy
        from collections import Counter
        counts = Counter(responses)
        total = len(responses)

        entropy = 0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * (p.bit_length() - 1)  # Approximate log2

        return entropy / len(responses) if responses else 0

    def estimate_confidence(self, prompt: str) -> float:
        """Estimate confidence from multiple samples"""
        answers = []
        confidences = []

        for _ in range(self.num_samples):
            answer, conf = self.model(prompt)
            answers.append(answer)
            confidences.append(conf)

        # Agreement-based confidence
        from collections import Counter
        most_common_count = Counter(answers).most_common(1)[0][1]
        agreement = most_common_count / len(answers)

        # Average model confidence
        avg_confidence = sum(confidences) / len(confidences)

        # Combined uncertainty
        uncertainty = 1 - (agreement * 0.7 + avg_confidence * 0.3)

        return uncertainty

    def estimate_disagreement(self, prompt: str) -> float:
        """Estimate disagreement between samples"""
        answers = []
        for _ in range(self.num_samples):
            answer, _ = self.model(prompt)
            answers.append(answer)

        unique_answers = len(set(answers))
        disagreement = (unique_answers - 1) / max(self.num_samples - 1, 1)

        return disagreement


class ActivePromptSelector:
    """
    Active-Prompt Selector
    ======================

    Selects examples for annotation based on uncertainty.
    """

    def __init__(self, uncertainty_estimator: UncertaintyEstimator = None):
        self.ue = uncertainty_estimator or UncertaintyEstimator()
        self.examples: List[ActivePromptExample] = []

    def add_example(
        self,
        question: str,
        answer: str,
        difficulty: float = None
    ):
        """Add an example"""
        example = ActivePromptExample(
            id=f"ex_{uuid.uuid4().hex[:8]}",
            question=question,
            answer=answer,
            difficulty=difficulty or random.uniform(0.3, 0.8)
        )
        self.examples.append(example)
        return example

    def estimate_uncertainty(self):
        """Estimate uncertainty for all examples"""
        for example in self.examples:
            uncertainty = self.ue.estimate_confidence(example.question)
            example.uncertainty = uncertainty

    def select_for_annotation(
        self,
        num_to_select: int = 5,
        strategy: str = "uncertainty"
    ) -> List[ActivePromptExample]:
        """Select examples for annotation"""
        if strategy == "uncertainty":
            # Select most uncertain
            sorted_examples = sorted(
                self.examples,
                key=lambda x: x.uncertainty,
                reverse=True
            )
        elif strategy == "difficulty":
            # Select most difficult
            sorted_examples = sorted(
                self.examples,
                key=lambda x: x.difficulty,
                reverse=True
            )
        elif strategy == "combined":
            # Combined score
            for ex in self.examples:
                ex.uncertainty = (ex.uncertainty + ex.difficulty) / 2
            sorted_examples = sorted(
                self.examples,
                key=lambda x: x.uncertainty,
                reverse=True
            )
        else:
            sorted_examples = self.examples

        # Return top k unannotated
        selected = [
            ex for ex in sorted_examples
            if not ex.annotated
        ][:num_to_select]

        return selected

    def select_diverse(
        self,
        num_to_select: int = 5
    ) -> List[ActivePromptExample]:
        """Select diverse examples based on difficulty"""
        if not self.examples:
            return []

        # Sort by difficulty
        sorted_by_diff = sorted(
            self.examples,
            key=lambda x: x.difficulty
        )

        # Select from different difficulty levels
        selected = []
        bucket_size = len(sorted_by_diff) // num_to_select

        for i in range(num_to_select):
            start = i * bucket_size
            end = start + bucket_size
            bucket = sorted_by_diff[start:end]

            if bucket:
                # Select most uncertain in bucket
                most_uncertain = max(bucket, key=lambda x: x.uncertainty)
                if not most_uncertain.annotated:
                    selected.append(most_uncertain)

        return selected


class ActivePromptEngine:
    """
    Active-Prompt Engine
    ====================

    Full active prompting system with iterative refinement.
    """

    def __init__(self):
        self.selector = ActivePromptSelector()
        self.iteration = 0
        self.history = []

    def initialize_examples(
        self,
        examples: List[Tuple[str, str]]
    ):
        """Initialize with examples"""
        for question, answer in examples:
            self.selector.add_example(question, answer)

    def run_iteration(
        self,
        model: Callable[[str, List], str] = None,
        annotate_fn: Callable[[str], Dict] = None
    ) -> Dict[str, Any]:
        """Run one iteration of active prompting"""
        model = model or (lambda p, ex: "Answer")
        annotate_fn = annotate_fn or self._default_annotate

        self.iteration += 1

        # Estimate uncertainty
        self.selector.estimate_uncertainty()

        # Select examples for annotation
        to_annotate = self.selector.select_for_annotation(
            num_to_select=3,
            strategy="combined"
        )

        # Annotate selected examples
        annotated = []
        for example in to_annotate:
            annotations = annotate_fn(example)
            example.annotations = annotations
            example.annotated = True
            annotated.append({
                "id": example.id,
                "question": example.question,
                "annotations": annotations
            })

        # Generate response with annotated examples
        # In practice, would use these in the prompt

        result = {
            "iteration": self.iteration,
            "annotated_count": len(annotated),
            "total_uncertainty": sum(e.uncertainty for e in self.selector.examples) / len(self.selector.examples),
            "annotated": annotated
        }

        self.history.append(result)
        return result

    def _default_annotate(self, example: ActivePromptExample) -> Dict:
        """Default annotation function"""
        return {
            "reasoning_steps": ["Step 1: Analyze", "Step 2: Solve"],
            "key_insights": ["Key point 1", "Key point 2"],
            "common_mistakes": ["Mistake 1"],
            "difficulty_level": "medium"
        }

    def get_statistics(self) -> Dict:
        """Get statistics"""
        return {
            "total_examples": len(self.selector.examples),
            "annotated_examples": sum(1 for e in self.selector.examples if e.annotated),
            "total_iterations": self.iteration,
            "avg_uncertainty": sum(e.uncertainty for e in self.selector.examples) / len(self.selector.examples) if self.selector.examples else 0
        }


class DifficultyEstimator:
    """
    Difficulty Estimator
    ====================

    Estimates difficulty of examples.
    """

    def __init__(self):
        pass

    def estimate_difficulty(
        self,
        question: str,
        answer: str = None
    ) -> float:
        """Estimate difficulty of a question"""
        difficulty = 0.5

        # Length-based difficulty
        word_count = len(question.split())
        if word_count > 50:
            difficulty += 0.1
        elif word_count < 10:
            difficulty -= 0.1

        # Complexity indicators
        complexity_indicators = [
            "analyze", "compare", "evaluate", "synthesize",
            "explain why", "prove", "derive"
        ]
        for indicator in complexity_indicators:
            if indicator in question.lower():
                difficulty += 0.1

        # Numeric difficulty
        import re
        numbers = re.findall(r'\d+', question)
        if len(numbers) > 3:
            difficulty += 0.15

        return min(max(difficulty, 0.0), 1.0)

    def categorize_difficulty(self, difficulty: float) -> str:
        """Categorize difficulty level"""
        if difficulty < 0.3:
            return "easy"
        elif difficulty < 0.6:
            return "medium"
        elif difficulty < 0.8:
            return "hard"
        else:
            return "very_hard"


# Demo function
def demo():
    """Demonstrate Active-Prompt"""
    print("=" * 60)
    print("  Active-Prompt Demo")
    print("=" * 60)

    # Mock model
    def mock_model(prompt: str):
        answers = ["A", "B", "C", "D"]
        return random.choice(answers), random.uniform(0.6, 0.95)

    # Initialize examples
    examples = [
        ("What is 2 + 2?", "4"),
        ("Explain quantum entanglement", "Complex physics concept..."),
        ("What is the capital of France?", "Paris"),
        ("Compare machine learning and deep learning", "Detailed comparison..."),
        ("Calculate the derivative of x^2", "2x"),
    ]

    # Create engine
    engine = ActivePromptEngine()
    engine.initialize_examples(examples)

    print("\n1. Initial Examples:")
    for ex in engine.selector.examples:
        print(f"  - {ex.question[:40]}...")

    # Run iterations
    print("\n2. Running Iterations:")
    for i in range(3):
        result = engine.run_iteration()
        print(f"  Iteration {result['iteration']}: annotated {result['annotated_count']} examples")

    # Statistics
    print("\n3. Statistics:")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Difficulty estimation
    print("\n" + "-" * 50)
    print("4. Difficulty Estimation:")

    de = DifficultyEstimator()
    test_questions = [
        "What is 2 + 2?",
        "Explain the theory of relativity",
        "Compare and contrast photosynthesis and respiration",
    ]

    for q in test_questions:
        diff = de.estimate_difficulty(q)
        cat = de.categorize_difficulty(diff)
        print(f"  '{q[:40]}...' -> {cat} ({diff:.2f})")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()