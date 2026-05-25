"""
Day 52: Chain of Thought
========================
Step-by-step reasoning for complex problem solving.

Key Concepts:
- Reasoning chains
- Intermediate steps
- Reasoning verification
- Self-consistency
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import uuid


class ReasoningType(Enum):
    """Types of reasoning strategies"""
    LINEAR = "linear"  # Step by step
    BRANCHING = "branching"  # Multiple paths
    VERIFICATION = "verification"  # Check and correct
    REFLECTIVE = "reflective"  # Think about thinking


@dataclass
class ReasoningStep:
    """A single step in reasoning"""
    id: str
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 1.0
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """A chain of reasoning steps"""
    id: str
    problem: str
    steps: List[ReasoningStep] = field(default_factory=list)
    result: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    reasoning_type: ReasoningType = ReasoningType.LINEAR

    def add_step(
        self,
        thought: str,
        action: str = None,
        observation: str = None,
        confidence: float = 1.0
    ) -> ReasoningStep:
        """Add a step to the chain"""
        step = ReasoningStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            step_number=len(self.steps) + 1,
            thought=thought,
            action=action,
            observation=observation,
            confidence=confidence
        )
        self.steps.append(step)
        return step

    def get_thought_process(self) -> str:
        """Get the full thought process as text"""
        lines = []
        for step in self.steps:
            lines.append(f"Step {step.step_number}: {step.thought}")
            if step.action:
                lines.append(f"  Action: {step.action}")
            if step.observation:
                lines.append(f"  Observation: {step.observation}")
        return "\n".join(lines)

    def mark_final(self, result: str):
        """Mark the chain as complete"""
        if self.steps:
            self.steps[-1].is_final = True
        self.result = result


class ChainOfThought:
    """
    Chain of Thought Reasoner
    =========================

    Implements step-by-step reasoning for complex problems.
    """

    def __init__(
        self,
        reasoner: Callable[[str], str] = None,
        max_steps: int = 10,
        include_observations: bool = True
    ):
        self.reasoner = reasoner or self._default_reasoner
        self.max_steps = max_steps
        self.include_observations = include_observations

    def _default_reasoner(self, prompt: str) -> str:
        """Default reasoner (simulated)"""
        # In production, this would call an LLM
        return "Based on the analysis..."

    def solve(
        self,
        problem: str,
        system_prompt: str = None
    ) -> ReasoningChain:
        """Solve a problem using chain of thought"""
        chain = ReasoningChain(
            id=f"chain_{uuid.uuid4().hex[:8]}",
            problem=problem,
            reasoning_type=ReasoningType.LINEAR
        )

        # Initial prompt
        current_state = problem
        step_count = 0

        while step_count < self.max_steps:
            # Build reasoning prompt
            prompt = self._build_reasoning_prompt(
                problem,
                chain,
                system_prompt
            )

            # Get response
            response = self.reasoner(prompt)

            # Parse response
            step = self._parse_response(response, chain)
            if not step:
                break

            chain.add_step(
                thought=step["thought"],
                action=step.get("action"),
                observation=step.get("observation"),
                confidence=step.get("confidence", 1.0)
            )

            # Check if done
            if step.get("is_final"):
                chain.mark_final(step.get("result", response))
                break

            step_count += 1
            current_state = response

        return chain

    def _build_reasoning_prompt(
        self,
        problem: str,
        chain: ReasoningChain,
        system_prompt: str = None
    ) -> str:
        """Build the prompt for each step"""
        prompt_parts = []

        if system_prompt:
            prompt_parts.append(system_prompt)

        prompt_parts.append(f"Problem: {problem}")

        if chain.steps:
            prompt_parts.append("\nPrevious reasoning:")
            for step in chain.steps:
                prompt_parts.append(f"Step {step.step_number}: {step.thought}")
                if step.observation:
                    prompt_parts.append(f"  Result: {step.observation}")

        prompt_parts.append(
            "\nThink step by step. Provide your next thought, "
            "any action to take, and the observation from that action."
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str, chain: ReasoningChain) -> Dict:
        """Parse LLM response into steps"""
        # Simple parsing - in production use more robust methods
        lines = response.split("\n")

        thought = response
        action = None
        observation = None
        is_final = False
        result = None

        # Look for markers
        if "FINAL ANSWER:" in response:
            parts = response.split("FINAL ANSWER:")
            thought = parts[0].strip()
            result = parts[1].strip()
            is_final = True
        elif "therefore" in response.lower() or "conclusion" in response.lower():
            is_final = True
            result = response

        return {
            "thought": thought,
            "action": action,
            "observation": observation,
            "is_final": is_final,
            "result": result,
            "confidence": 1.0
        }


class TreeofThoughts:
    """
    Tree of Thoughts
    ================

    Explore multiple reasoning paths simultaneously.
    """

    def __init__(
        self,
        reasoner: Callable[[str], str] = None,
        num_branches: int = 3,
        depth: int = 3
    ):
        self.reasoner = reasoner or ChainOfThought()._default_reasoner
        self.num_branches = num_branches
        self.depth = depth

    def solve(
        self,
        problem: str,
        evaluation_fn: Callable[[str], float] = None
    ) -> Tuple[ReasoningChain, float]:
        """Solve with tree of thoughts"""
        evaluation_fn = evaluation_fn or (lambda x: 1.0)

        # Start with initial thoughts
        current_level = [problem]
        best_chain = None
        best_score = -float("inf")

        for depth in range(self.depth):
            next_level = []

            for state in current_level:
                # Generate multiple branches
                branches = self._generate_branches(state)

                for branch in branches:
                    # Evaluate branch
                    score = evaluation_fn(branch)

                    if score > best_score:
                        best_score = score
                        best_chain = self._create_chain(problem, branch)

                    next_level.append(branch)

            current_level = next_level[:self.num_branches]

        return best_chain, best_score

    def _generate_branches(self, state: str) -> List[str]:
        """Generate branching thoughts"""
        prompt = f"""Given this state: {state}

Generate {self.num_branches} different approaches or next steps.
List each on a new line."""

        response = self.reasoner(prompt)
        branches = [state + "\n" + line for line in response.split("\n") if line.strip()]

        return branches[:self.num_branches]

    def _create_chain(self, problem: str, solution: str) -> ReasoningChain:
        """Create a reasoning chain from solution"""
        chain = ReasoningChain(
            id=f"chain_{uuid.uuid4().hex[:8]}",
            problem=problem,
            reasoning_type=ReasoningType.BRANCHING
        )
        chain.mark_final(solution)
        return chain


class VerificationChain:
    """
    Verification Chain
    ==================

    Reasoning with self-verification at each step.
    """

    def __init__(self, reasoner: Callable[[str], str] = None):
        self.reasoner = reasoner or ChainOfThought()._default_reasoner

    def solve(self, problem: str) -> ReasoningChain:
        """Solve with verification"""
        chain = ReasoningChain(
            id=f"chain_{uuid.uuid4().hex[:8]}",
            problem=problem,
            reasoning_type=ReasoningType.VERIFICATION
        )

        current_state = problem
        max_iterations = 5

        for i in range(max_iterations):
            # Generate next step
            prompt = f"""Problem: {problem}
Current state: {current_state}

Provide the next step in solving this problem."""

            step = self.reasoner(prompt)
            chain.add_step(thought=step)

            # Verify step
            verify_prompt = f"""Verify this step: {step}
For the problem: {problem}

Is this step correct and helpful? Answer yes or no and explain."""

            verification = self.reasoner(verify_prompt)

            if "yes" in verification.lower() and ("conclusion" in verification.lower() or "therefore" in verification.lower()):
                chain.mark_final(step)
                break

            current_state = step

        return chain


# Demo function
def demo():
    """Demonstrate Chain of Thought"""
    print("=" * 60)
    print("  Chain of Thought Demo")
    print("=" * 60)

    # Create a reasoner (simulated)
    def mock_reasoner(prompt: str) -> str:
        responses = [
            "Let me break this down. First, I need to identify the key components...",
            "Step 1: Analyze the problem structure.\nStep 2: Apply the appropriate method.\nObservation: This approach yields the solution.",
            "Therefore, the answer is 42. FINAL ANSWER: 42"
        ]
        import random
        return random.choice(responses)

    # Chain of Thought
    print("\n1. Chain of Thought:")
    cot = ChainOfThought(reasoner=mock_reasoner, max_steps=3)

    problem = "If a train travels 120km in 2 hours, what is its speed?"
    chain = cot.solve(problem)

    print(f"Problem: {problem}")
    print(f"\nReasoning Process:")
    print(chain.get_thought_process())
    print(f"\nFinal Result: {chain.result}")

    # Tree of Thoughts
    print("\n" + "-" * 50)
    print("2. Tree of Thoughts:")
    tot = TreeofThoughts(reasoner=mock_reasoner, num_branches=2, depth=2)

    problem2 = "Find the best way to organize a team of 5 people"
    chain2, score = tot.solve(problem2)

    print(f"Problem: {problem2}")
    print(f"Best score: {score:.2f}")
    print(f"Result: {chain2.result}")

    # Verification Chain
    print("\n" + "-" * 50)
    print("3. Verification Chain:")
    vc = VerificationChain(reasoner=mock_reasoner)

    problem3 = "Calculate 15 * 15"
    chain3 = vc.solve(problem3)

    print(f"Problem: {problem3}")
    print(f"Steps: {len(chain3.steps)}")
    print(f"Result: {chain3.result}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()