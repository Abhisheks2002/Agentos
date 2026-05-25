"""
Day 51: Few-Shot Examples
=========================
In-context learning through carefully selected examples.

Key Concepts:
- Example selection strategies
- Example formatting
- Dynamic few-shot
- Curriculum learning
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random
import uuid


@dataclass
class Example:
    """A few-shot example"""
    id: str
    input_text: str
    output_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # Quality score


@dataclass
class FewShotConfig:
    """Configuration for few-shot learning"""
    num_examples: int = 3
    selection_strategy: str = "random"  # random, similarity, diversity
    format_template: str = "input_output"  # input_output, qa, demonstration
    include_reasoning: bool = False
    max_example_length: int = 500


class ExampleSelector:
    """Base class for selecting examples"""

    def select(
        self,
        examples: List[Example],
        query: str,
        num_examples: int
    ) -> List[Example]:
        raise NotImplementedError


class RandomSelector(ExampleSelector):
    """Random example selection"""

    def select(
        self,
        examples: List[Example],
        query: str,
        num_examples: int
    ) -> List[Example]:
        return random.sample(
            examples,
            min(num_examples, len(examples))
        )


class SimilaritySelector(ExampleSelector):
    """Select examples by similarity to query"""

    def __init__(self, similarity_fn: Callable[[str, str], float] = None):
        self.similarity_fn = similarity_fn or self._default_similarity

    def _default_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1 & words2)
        return overlap / min(len(words1), len(words2))

    def select(
        self,
        examples: List[Example],
        query: str,
        num_examples: int
    ) -> List[Example]:
        # Score each example by similarity
        scored = []
        for ex in examples:
            score = self.similarity_fn(query, ex.input_text)
            scored.append((score, ex))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [ex for _, ex in scored[:num_examples]]


class DiversitySelector(ExampleSelector):
    """Select diverse examples to cover different patterns"""

    def __init__(self, similarity_fn: Callable[[str, str], float] = None):
        self.similarity_fn = similarity_fn or self._default_similarity
        self._default_similarity = SimilaritySelector()._default_similarity

    def select(
        self,
        examples: List[Example],
        query: str,
        num_examples: int
    ) -> List[Example]:
        if len(examples) <= num_examples:
            return examples

        selected = []
        remaining = list(examples)

        # First select most similar to query
        query_similarities = [
            (self.similarity_fn(query, ex.input_text), ex)
            for ex in remaining
        ]
        query_similarities.sort(reverse=True)

        if query_similarities:
            selected.append(query_similarities[0][1])
            remaining.remove(selected[0])

        # Then add most diverse from selected
        while len(selected) < num_examples and remaining:
            best_score = -1
            best_example = None

            for ex in remaining:
                # Minimum similarity to all selected (maximize diversity)
                min_sim = min(
                    self.similarity_fn(selected[i].input_text, ex.input_text)
                    for i in range(len(selected))
                )
                if min_sim > best_score:
                    best_score = min_sim
                    best_example = ex

            if best_example:
                selected.append(best_example)
                remaining.remove(best_example)
            else:
                break

        return selected


class SemanticSelector(ExampleSelector):
    """Select examples using semantic embeddings (simulated)"""

    def select(
        self,
        examples: List[Example],
        query: str,
        num_examples: int
    ) -> List[Example]:
        # Simulate embedding similarity
        # In production, use actual embeddings

        def get_embedding(text: str) -> List[float]:
            import hashlib
            h = hashlib.sha256(text.encode()).digest()
            return [b / 255.0 for b in h[:32]]

        query_emb = get_embedding(query)
        example_scores = []

        for ex in examples:
            ex_emb = get_embedding(ex.input_text)
            # Cosine similarity
            dot = sum(a * b for a, b in zip(query_emb, ex_emb))
            mag = (sum(a * a for a in query_emb) * sum(b * b for b in ex_emb)) ** 0.5
            score = dot / mag if mag > 0 else 0
            example_scores.append((score, ex))

        example_scores.sort(reverse=True)
        return [ex for _, ex in example_scores[:num_examples]]


class FewShotPrompter:
    """
    Few-Shot Prompter
    ==================

    Formats examples and builds prompts with in-context learning.
    """

    SELECTORS = {
        "random": RandomSelector,
        "similarity": SimilaritySelector,
        "diversity": DiversitySelector,
        "semantic": SemanticSelector
    }

    FORMATTERS = {
        "input_output": lambda ex: f"Input: {ex.input_text}\nOutput: {ex.output_text}",
        "qa": lambda ex: f"Q: {ex.input_text}\nA: {ex.output_text}",
        "demonstration": lambda ex: f"{ex.input_text}\n→ {ex.output_text}",
        "conversation": lambda ex: f"User: {ex.input_text}\nAssistant: {ex.output_text}"
    }

    def __init__(self, config: FewShotConfig = None):
        self.config = config or FewShotConfig()
        self.examples: List[Example] = []

        # Create selector
        self.selector = self.SELECTORS.get(
            self.config.selection_strategy,
            RandomSelector
        )()

    def add_example(self, input_text: str, output_text: str, metadata: Dict = None):
        """Add an example to the pool"""
        example = Example(
            id=f"ex_{uuid.uuid4().hex[:8]}",
            input_text=input_text,
            output_text=output_text,
            metadata=metadata or {}
        )
        self.examples.append(example)

    def add_examples(self, examples: List[Tuple[str, str]]):
        """Add multiple examples"""
        for input_text, output_text in examples:
            self.add_example(input_text, output_text)

    def build_prompt(
        self,
        query: str,
        system_prompt: str = None,
        include_examples: bool = True
    ) -> str:
        """Build a prompt with few-shot examples"""
        parts = []

        # System prompt
        if system_prompt:
            parts.append(f"System: {system_prompt}")

        # Examples
        if include_examples and self.examples:
            selected = self.selector.select(
                self.examples,
                query,
                self.config.num_examples
            )

            formatter = self.FORMATTERS.get(
                self.config.format_template,
                self.FORMATTERS["input_output"]
            )

            parts.append("Examples:")
            for ex in selected:
                formatted = formatter(ex)
                parts.append(formatted)

        # Query
        if self.config.format_template == "qa":
            parts.append(f"Q: {query}")
        else:
            parts.append(f"Input: {query}")

        return "\n\n".join(parts)

    def get_example_string(self, query: str) -> str:
        """Get formatted examples only"""
        selected = self.selector.select(
            self.examples,
            query,
            self.config.num_examples
        )

        formatter = self.FORMATTERS.get(
            self.config.format_template,
            self.FORMATTERS["input_output"]
        )

        return "\n\n".join(formatter(ex) for ex in selected)

    def select_best_examples(self, query: str) -> List[Example]:
        """Get the best examples for a query"""
        return self.selector.select(
            self.examples,
            query,
            self.config.num_examples
        )


class DynamicFewShot:
    """
    Dynamic Few-Shot
    =================

    Adaptively selects examples based on query characteristics.
    """

    def __init__(self):
        self.prompters: Dict[str, FewShotPrompter] = {}

    def register_domain(
        self,
        domain: str,
        examples: List[Tuple[str, str]],
        config: FewShotConfig = None
    ):
        """Register examples for a domain"""
        prompter = FewShotPrompter(config)
        prompter.add_examples(examples)
        self.prompters[domain] = prompter

    def get_prompt(self, domain: str, query: str) -> str:
        """Get prompt for domain and query"""
        prompter = self.prompters.get(domain)
        if not prompter:
            return query
        return prompter.build_prompt(query)

    def detect_domain(self, query: str) -> str:
        """Detect the domain of a query"""
        domain_keywords = {
            "coding": ["code", "function", "class", "python", "javascript", "debug"],
            "math": ["calculate", "solve", "equation", "compute", "math"],
            "writing": ["write", "essay", "article", "story", "creative"],
            "analysis": ["analyze", "compare", "explain", "why", "how"]
        }

        query_lower = query.lower()
        best_domain = "general"
        best_score = 0

        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > best_score:
                best_score = score
                best_domain = domain

        return best_domain


# Demo function
def demo():
    """Demonstrate Few-Shot Examples"""
    print("=" * 60)
    print("  Few-Shot Examples Demo")
    print("=" * 60)

    # Create examples for sentiment analysis
    examples = [
        ("This product is amazing! Best purchase ever.", "positive"),
        ("Terrible experience. Would not recommend.", "negative"),
        ("It's okay, nothing special.", "neutral"),
        ("Absolutely love it! Five stars!", "positive"),
        ("Very disappointing. Waste of money.", "negative"),
    ]

    # Create few-shot prompter
    config = FewShotConfig(
        num_examples=3,
        selection_strategy="similarity",
        format_template="qa"
    )
    prompter = FewShotPrompter(config)
    prompter.add_examples(examples)

    # Test queries
    test_queries = [
        "The service was fantastic! Highly satisfied.",
        "Not worth the price. Very unhappy.",
        "Average product, does what it says."
    ]

    print("\n1. Building Prompts with Examples:")
    for query in test_queries:
        prompt = prompter.build_prompt(query, "Classify the sentiment.")
        print(f"\nQuery: {query}")
        print(f"Prompt:\n{prompt}")
        print("-" * 40)

    # Test different selectors
    print("\n2. Different Selection Strategies:")
    for strategy in ["random", "similarity", "diversity"]:
        config = FewShotConfig(
            num_examples=3,
            selection_strategy=strategy
        )
        prompter = FewShotPrompter(config)
        prompter.add_examples(examples)

        selected = prompter.select_best_examples("This is great!")
        print(f"\n{strategy}: {[ex.output_text for ex in selected]}")

    # Test dynamic few-shot
    print("\n3. Dynamic Few-Shot:")
    dynamic = DynamicFewShot()
    dynamic.register_domain("coding", [
        ("Write a function to add numbers", "def add(a, b):\n    return a + b"),
        ("Create a class for a car", "class Car:\n    def __init__(self, make, model):\n        self.make = make\n        self.model = model"),
    ])
    dynamic.register_domain("writing", [
        ("Write a haiku", "Morning light spreads\nGolden rays touch the earth\nDay begins anew"),
        ("Write a limerick", "There once was a cat from Nantucket"),
    ])

    for query in ["Write a function to sort a list", "Write a poem about the sun"]:
        domain = dynamic.detect_domain(query)
        prompt = dynamic.get_prompt(domain, query)
        print(f"Query: {query}")
        print(f"Domain: {domain}")
        print(f"Prompt: {prompt[:80]}...")
        print("-" * 30)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()