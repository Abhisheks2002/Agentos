"""
Day 54: Meta-Prompting
======================
Self-referential prompts and prompt improvement.

Key Concepts:
- Self-reflective prompts
- Prompt optimization
- Automatic prompt engineering
- Prompt mutation and selection
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import uuid
import random


@dataclass
class Prompt:
    """A prompt with metadata"""
    id: str
    content: str
    version: int = 1
    score: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None


@dataclass
class PromptEvolution:
    """Track prompt evolution"""
    prompt: Prompt
    mutations: List[str] = field(default_factory=list)
    feedback: str = ""


class MetaPrompter:
    """
    Meta-Prompter
    =============

    Uses AI to improve prompts through self-reflection.
    """

    def __init__(
        self,
        llm: Callable[[str], str] = None,
        max_iterations: int = 5
    ):
        self.llm = llm or self._default_llm
        self.max_iterations = max_iterations
        self.prompt_history: List[Prompt] = []

    def _default_llm(self, prompt: str) -> str:
        """Default LLM (simulated)"""
        responses = [
            "Here is an improved prompt:",
            "Consider refining the prompt with more specific instructions.",
            "The prompt could be clearer with better structure.",
        ]
        return random.choice(responses)

    def create_initial_prompt(self, task: str) -> Prompt:
        """Create an initial prompt for a task"""
        prompt_content = f"""Task: {task}

Please provide a detailed, step-by-step solution."""

        prompt = Prompt(
            id=f"prompt_{uuid.uuid4().hex[:8]}",
            content=prompt_content
        )
        self.prompt_history.append(prompt)
        return prompt

    def improve_prompt(
        self,
        prompt: Prompt,
        feedback: str = None,
        context: str = None
    ) -> Prompt:
        """Improve a prompt using meta-prompting"""
        improvement_prompt = self._build_improvement_prompt(
            prompt, feedback, context
        )

        # Get improved prompt from LLM
        response = self.llm(improvement_prompt)

        # Extract improved prompt
        improved_content = self._extract_improved_prompt(response)

        # Create new version
        new_prompt = Prompt(
            id=f"prompt_{uuid.uuid4().hex[:8]}",
            content=improved_content,
            version=prompt.version + 1,
            parent_id=prompt.id
        )

        self.prompt_history.append(new_prompt)
        return new_prompt

    def _build_improvement_prompt(
        self,
        prompt: Prompt,
        feedback: str,
        context: str
    ) -> str:
        """Build prompt for improvement"""
        parts = [
            "You are a prompt engineering expert.",
            f"Current prompt:\n{prompt.content}",
        ]

        if feedback:
            parts.append(f"Feedback on current prompt:\n{feedback}")

        if context:
            parts.append(f"Context:\n{context}")

        parts.append(
            "Improve this prompt to get better results. "
            "Consider: clarity, specificity, structure, and examples. "
            "Provide the improved prompt in your response."
        )

        return "\n\n".join(parts)

    def _extract_improved_prompt(self, response: str) -> str:
        """Extract the improved prompt from LLM response"""
        # Look for markdown code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)

        if code_blocks:
            return code_blocks[0].strip()

        # Look for "Improved prompt:" section
        if "improved prompt:" in response.lower():
            parts = response.split("improved prompt:", 1)
            if len(parts) > 1:
                return parts[1].strip()

        # Return original with modifications noted
        return response.strip()

    def optimize(
        self,
        task: str,
        evaluate_fn: Callable[[str, Prompt], float] = None,
        context: str = None
    ) -> Tuple[Prompt, List[Prompt]]:
        """Auto-optimize a prompt through iterations"""
        evaluate_fn = evaluate_fn or (lambda x, p: 0.5)

        # Start with initial prompt
        current = self.create_initial_prompt(task)

        history = [current]
        best = current
        best_score = 0.0

        for i in range(self.max_iterations):
            # Evaluate current prompt
            score = evaluate_fn(task, current)

            if score > best_score:
                best_score = score
                best = current

            current.metrics["score"] = score
            current.metrics["iteration"] = i + 1

            # Generate feedback based on score
            feedback = self._generate_feedback(score, current)

            # Improve
            current = self.improve_prompt(current, feedback, context)
            history.append(current)

        return best, history

    def _generate_feedback(self, score: float, prompt: Prompt) -> str:
        """Generate feedback based on score"""
        if score > 0.8:
            return "The prompt is working well. Minor improvements could help."
        elif score > 0.5:
            return "The prompt is acceptable but could be clearer."
        else:
            return "The prompt needs significant improvement in clarity."


class PromptMutator:
    """
    Prompt Mutator
    ==============

    Mutates prompts using various strategies.
    """

    MUTATION_STRATEGIES = [
        "add_constraints",
        "add_examples",
        "simplify",
        "add_structure",
        "add_role",
        "add_formatting",
        "add_reasoning",
        "specify_persona"
    ]

    def __init__(self):
        self.mutation_templates = self._init_templates()

    def _init_templates(self) -> Dict[str, Callable[[str], str]]:
        """Initialize mutation templates"""
        return {
            "add_constraints": lambda p: p + "\n\nConstraints: Provide exact, precise answers.",
            "add_examples": lambda p: p + "\n\nExample: Think step by step, show your work.",
            "simplify": lambda p: f"Simplify this request: {p}\n\nProvide a clear, concise response.",
            "add_structure": lambda p: p + "\n\nFormat your response with clear sections and bullet points.",
            "add_role": lambda p: f"You are an expert in your field. {p}",
            "add_formatting": lambda p: p + "\n\nRespond in JSON format where applicable.",
            "add_reasoning": lambda p: p + "\n\nExplain your reasoning before providing the answer.",
            "add_persona": lambda p: f"As a wise mentor, {p.lower()}"
        }

    def mutate(
        self,
        prompt: Prompt,
        strategy: str = None,
        custom_mutation: Callable[[str], str] = None
    ) -> Prompt:
        """Mutate a prompt using a strategy"""
        if strategy is None:
            strategy = random.choice(self.MUTATION_STRATEGIES)

        if strategy == "custom" and custom_mutation:
            new_content = custom_mutation(prompt.content)
        elif strategy in self.mutation_templates:
            new_content = self.mutation_templates[strategy](prompt.content)
        else:
            new_content = prompt.content

        new_prompt = Prompt(
            id=f"prompt_{uuid.uuid4().hex[:8]}",
            content=new_content,
            version=prompt.version + 1,
            parent_id=prompt.id,
            metrics={"mutation_strategy": strategy}
        )

        return new_prompt

    def crossover(self, prompt1: Prompt, prompt2: Prompt) -> Prompt:
        """Create a new prompt by combining two prompts"""
        lines1 = prompt1.content.split("\n")
        lines2 = prompt2.content.split("\n")

        # Simple crossover: take first half from one, second from other
        mid1 = len(lines1) // 2
        mid2 = len(lines2) // 2

        new_lines = lines1[:mid1] + lines2[mid2:]
        new_content = "\n".join(new_lines)

        return Prompt(
            id=f"prompt_{uuid.uuid4().hex[:8]}",
            content=new_content,
            version=max(prompt1.version, prompt2.version) + 1,
            parent_id=prompt1.id,
            metrics={"crossover": True}
        )


class PromptSelector:
    """
    Prompt Selector
    ===============

    Selects best prompts based on evaluation.
    """

    def __init__(self):
        self.prompts: List[Prompt] = []

    def add_prompt(self, prompt: Prompt):
        """Add a prompt to the pool"""
        self.prompts.append(prompt)

    def select_best(
        self,
        evaluate_fn: Callable[[Prompt], float] = None,
        top_k: int = 1
    ) -> List[Prompt]:
        """Select best prompts"""
        if not self.prompts:
            return []

        if evaluate_fn:
            for p in self.prompts:
                p.score = evaluate_fn(p)

        sorted_prompts = sorted(self.prompts, key=lambda p: p.score, reverse=True)
        return sorted_prompts[:top_k]

    def tournament_select(self, tournament_size: int = 4) -> Prompt:
        """Select using tournament selection"""
        if not self.prompts:
            raise ValueError("No prompts available")

        tournament = random.sample(self.prompts, min(tournament_size, len(self.prompts)))
        return max(tournament, key=lambda p: p.score)


# Demo function
def demo():
    """Demonstrate Meta-Prompting"""
    print("=" * 60)
    print("  Meta-Prompting Demo")
    print("=" * 60)

    # Mock LLM for demo
    def mock_llm(prompt: str) -> str:
        return f"""Improved prompt:

{prompt}

I have refined this prompt for better clarity and specificity.
The key improvements focus on structure and actionable instructions."""

    # Meta-prompter
    print("\n1. Meta-Prompter:")
    metaprompter = MetaPrompter(llm=mock_llm, max_iterations=3)

    task = "Write a function to calculate factorial"

    # Simple evaluation
    def evaluate(task: str, prompt: Prompt) -> float:
        score = 0.5
        if "step" in prompt.content.lower() or "detail" in prompt.content.lower():
            score += 0.2
        if "function" in task.lower() and "function" in prompt.content.lower():
            score += 0.2
        return min(score, 1.0)

    best, history = metaprompter.optimize(task, evaluate)

    print(f"Task: {task}")
    print(f"\nOptimization history:")
    for i, p in enumerate(history):
        print(f"  v{p.version}: score={p.metrics.get('score', 'N/A'):.2f}")

    print(f"\nBest prompt (v{best.version}):")
    print(f"  {best.content[:100]}...")

    # Prompt Mutator
    print("\n" + "-" * 50)
    print("2. Prompt Mutator:")

    mutator = PromptMutator()
    original = Prompt(id="test", content="Solve this math problem")

    for strategy in ["add_constraints", "add_role", "add_structure"]:
        mutated = mutator.mutate(original, strategy)
        print(f"\n{strategy}:")
        print(f"  {mutated.content[:80]}...")

    # Prompt Selector
    print("\n" + "-" * 50)
    print("3. Prompt Selector:")

    selector = PromptSelector()
    for i in range(5):
        p = Prompt(
            id=f"p{i}",
            content=f"Prompt version {i+1}",
            score=random.uniform(0.3, 0.9)
        )
        selector.add_prompt(p)

    best_prompts = selector.select_best(top_k=3)
    print(f"Top 3 prompts: {[p.score for p in best_prompts]}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()