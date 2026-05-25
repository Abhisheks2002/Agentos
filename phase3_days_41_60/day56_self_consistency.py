"""
Day 56: Self-Consistency
========================
Multiple reasoning paths voting for best answer.

Key Concepts:
- Generate diverse reasoning paths
- Vote on final answer
- Aggregate predictions
- Consistency scoring
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import random
import uuid


@dataclass
class ReasoningPath:
    """A reasoning path with its conclusion"""
    id: str
    reasoning: str
    conclusion: str
    confidence: float = 1.0
    token_count: int = 0


@dataclass
class SelfConsistencyResult:
    """Result of self-consistency voting"""
    final_answer: str
    total_paths: int
    consistent_paths: int
    consistency_score: float
    path_votes: Dict[str, int]
    details: Dict[str, Any] = field(default_factory=dict)


class SelfConsistency:
    """
    Self-Consistency
    ================

    Generate multiple reasoning paths and vote on the best.
    """

    def __init__(
        self,
        generator: Callable[[str], str] = None,
        num_paths: int = 5,
        temperature: float = 0.7
    ):
        self.generator = generator or self._default_generator
        self.num_paths = num_paths
        self.temperature = temperature

    def _default_generator(self, prompt: str) -> str:
        """Default generator (simulated)"""
        return "Based on reasoning, the answer is: " + str(random.choice([1, 2, 3]))

    def generate_paths(self, problem: str) -> List[ReasoningPath]:
        """Generate multiple reasoning paths"""
        paths = []

        for i in range(self.num_paths):
            # Generate reasoning path
            prompt = f"Problem: {problem}\nProvide step-by-step reasoning."

            reasoning = self.generator(prompt)
            conclusion = self._extract_conclusion(reasoning)

            path = ReasoningPath(
                id=f"path_{uuid.uuid4().hex[:8]}",
                reasoning=reasoning,
                conclusion=conclusion,
                confidence=random.uniform(0.5, 1.0),
                token_count=len(reasoning.split())
            )
            paths.append(path)

        return paths

    def _extract_conclusion(self, reasoning: str) -> str:
        """Extract conclusion from reasoning"""
        # Look for explicit conclusion markers
        markers = [
            "therefore",
            "thus",
            "conclusion",
            "answer is",
            "final answer",
            "result:"
        ]

        reasoning_lower = reasoning.lower()

        for marker in markers:
            idx = reasoning_lower.find(marker)
            if idx != -1:
                # Extract the conclusion
                conclusion = reasoning[idx + len(marker):].strip()
                # Clean up
                conclusion = conclusion.split("\n")[0][:100]
                if conclusion:
                    return conclusion

        # Fallback: use last sentence
        sentences = reasoning.split(".")
        if sentences:
            return sentences[-2].strip() if len(sentences) > 1 else sentences[-1].strip()

        return reasoning[:100]

    def vote(self, paths: List[ReasoningPath]) -> SelfConsistencyResult:
        """Vote on the best conclusion"""
        # Count votes for each conclusion
        conclusions = [p.conclusion for p in paths]
        vote_counts = Counter(conclusions)

        # Get most voted conclusion
        most_common = vote_counts.most_common(1)[0]
        final_answer = most_common[0]
        consistent_paths = most_common[1]

        # Calculate consistency score
        consistency_score = consistent_paths / len(paths) if paths else 0

        # Weight by confidence
        weighted_votes = {}
        for path in paths:
            key = path.conclusion
            weighted_votes[key] = weighted_votes.get(key, 0) + path.confidence

        weighted_winner = max(weighted_votes, key=weighted_votes.get)

        return SelfConsistencyResult(
            final_answer=final_answer,
            total_paths=len(paths),
            consistent_paths=consistent_paths,
            consistency_score=consistency_score,
            path_votes=dict(vote_counts),
            details={
                "weighted_winner": weighted_winner,
                "weighted_scores": weighted_votes,
                "confidence_avg": sum(p.confidence for p in paths) / len(paths)
            }
        )

    def solve(self, problem: str) -> SelfConsistencyResult:
        """Solve problem using self-consistency"""
        # Generate paths
        paths = self.generate_paths(problem)

        # Vote
        result = self.vote(paths)

        # Store paths in result for analysis
        result.details["paths"] = [
            {
                "id": p.id,
                "conclusion": p.conclusion,
                "confidence": p.confidence
            }
            for p in paths
        ]

        return result


class DiverseSampler:
    """
    Diverse Sampler
    ===============

    Samples diverse reasoning paths to increase coverage.
    """

    def __init__(
        self,
        generator: Callable[[str], str] = None,
        diversity_threshold: float = 0.3
    ):
        self.generator = generator or SelfConsistency()._default_generator
        self.diversity_threshold = diversity_threshold

    def generate_diverse_paths(
        self,
        problem: str,
        num_paths: int = 5
    ) -> List[ReasoningPath]:
        """Generate diverse reasoning paths"""
        paths = []

        for i in range(num_paths):
            # Vary the prompt to encourage diversity
            prompt = self._build_diverse_prompt(problem, i, num_paths)

            reasoning = self.generator(prompt)
            conclusion = self._extract_conclusion(reasoning)

            path = ReasoningPath(
                id=f"path_{uuid.uuid4().hex[:8]}",
                reasoning=reasoning,
                conclusion=conclusion,
                confidence=random.uniform(0.5, 1.0)
            )
            paths.append(path)

        return paths

    def _build_diverse_prompt(self, problem: str, index: int, total: int) -> str:
        """Build prompts with different framing"""
        framings = [
            "Think step by step",
            "Consider all possibilities",
            "Use logical deduction",
            "Work backwards from the answer",
            "Break into subproblems"
        ]

        framing = framings[index % len(framings)]
        return f"Problem: {problem}\n{framing}."

    def _extract_conclusion(self, reasoning: str) -> str:
        """Extract conclusion (same as SelfConsistency)"""
        markers = ["therefore", "thus", "conclusion", "answer is", "result:"]
        reasoning_lower = reasoning.lower()

        for marker in markers:
            idx = reasoning_lower.find(marker)
            if idx != -1:
                conclusion = reasoning[idx + len(marker):].strip()
                return conclusion.split("\n")[0][:100]

        return reasoning[-100:] if len(reasoning) > 100 else reasoning


class ConsensusFinder:
    """
    Consensus Finder
    ================

    Find consensus among multiple reasoning paths.
    """

    def __init__(self):
        pass

    def find_consensus(
        self,
        paths: List[ReasoningPath],
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Find consensus among paths"""
        if not paths:
            return {"has_consensus": False, "consensus": None, "score": 0}

        # Group similar conclusions
        conclusion_groups = self._group_conclusions(paths)

        # Find largest group
        largest_group = max(
            conclusion_groups.values(),
            key=lambda g: len(g)
        )

        consensus_score = len(largest_group) / len(paths)

        if consensus_score >= threshold:
            return {
                "has_consensus": True,
                "consensus": largest_group[0].conclusion if largest_group else None,
                "score": consensus_score,
                "group_size": len(largest_group),
                "total_paths": len(paths)
            }

        return {
            "has_consensus": False,
            "consensus": None,
            "score": consensus_score,
            "group_size": len(largest_group),
            "total_paths": len(paths)
        }

    def _group_conclusions(
        self,
        paths: List[ReasoningPath]
    ) -> Dict[str, List[ReasoningPath]]:
        """Group similar conclusions"""
        groups = {}

        for path in paths:
            # Use conclusion as key (in production, use semantic similarity)
            key = path.conclusion[:50]  # First 50 chars as key

            if key not in groups:
                groups[key] = []
            groups[key].append(path)

        return groups


class WeightedAggregator:
    """
    Weighted Aggregator
    ====================

    Aggregate predictions with confidence weighting.
    """

    def __init__(self):
        pass

    def aggregate(
        self,
        paths: List[ReasoningPath]
    ) -> Dict[str, Any]:
        """Aggregate predictions using confidence weights"""
        if not paths:
            return {"final": None, "confidence": 0, "details": {}}

        # Weight each path by confidence
        weighted_scores = Counter()

        for path in paths:
            conclusion_key = path.conclusion[:50]
            weighted_scores[conclusion_key] += path.confidence

        # Get weighted winner
        total_weight = sum(p.confidence for p in paths)
        winner_conclusion = max(weighted_scores, key=weighted_scores.get)
        winner_score = weighted_scores[winner_conclusion]

        return {
            "final": winner_conclusion,
            "confidence": winner_score / total_weight if total_weight > 0 else 0,
            "weighted_scores": dict(weighted_scores),
            "total_paths": len(paths)
        }


# Demo function
def demo():
    """Demonstrate Self-Consistency"""
    print("=" * 60)
    print("  Self-Consistency Demo")
    print("=" * 60)

    # Mock generator
    def mock_gen(prompt: str) -> str:
        answers = [
            "Step 1: Identify the problem. Step 2: Analyze options. Therefore, the answer is 42.",
            "Working through this: first consider X, then Y. Thus, result is 42.",
            "Analysis shows we need to calculate. The conclusion is 42.",
            "Let me solve this: 1 + 1 = 2, 2 + 40 = 42. Answer: 42.",
            "This requires careful thought. After reasoning, the answer is 42."
        ]
        return random.choice(answers)

    # Self-consistency
    print("\n1. Self-Consistency:")
    sc = SelfConsistency(generator=mock_gen, num_paths=5)

    problem = "What is 1 + 1 + 40?"
    result = sc.solve(problem)

    print(f"Problem: {problem}")
    print(f"Total paths: {result.total_paths}")
    print(f"Consistent paths: {result.consistent_paths}")
    print(f"Consistency score: {result.consistency_score:.2f}")
    print(f"Final answer: {result.final_answer}")

    # Diverse sampling
    print("\n" + "-" * 50)
    print("2. Diverse Sampling:")

    ds = DiverseSampler(generator=mock_gen)
    diverse_paths = ds.generate_diverse_paths(problem, num_paths=3)

    print(f"Generated {len(diverse_paths)} diverse paths")
    for i, p in enumerate(diverse_paths, 1):
        print(f"  Path {i}: {p.conclusion[:40]}...")

    # Consensus finding
    print("\n" + "-" * 50)
    print("3. Consensus Finder:")

    cf = ConsensusFinder()
    consensus = cf.find_consistency(diverse_paths, threshold=0.5)

    print(f"Has consensus: {consensus['has_consensus']}")
    print(f"Score: {consensus['score']:.2f}")

    # Weighted aggregation
    print("\n" + "-" * 50)
    print("4. Weighted Aggregator:")

    wa = WeightedAggregator()
    aggregated = wa.aggregate(diverse_paths)

    print(f"Final: {aggregated['final']}")
    print(f"Confidence: {aggregated['confidence']:.2f}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()