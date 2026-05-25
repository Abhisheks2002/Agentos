"""
Day 59: Reflective Reasoning
============================
Self-reflective reasoning where agents evaluate and improve their own thinking.

Key Concepts:
- Self-evaluation
- Error detection
- Thought refinement
- Meta-cognition
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ReflectionType(Enum):
    """Types of reflection"""
    AFTER_ACTION = "after_action"  # Reflect after completing a task
    DURING_THINKING = "during_thinking"  # Reflect during reasoning
    ERROR_ANALYSIS = "error_analysis"  # Analyze and learn from errors
    SUCCESS_ANALYSIS = "success_analysis"  # Analyze what worked well


@dataclass
class Thought:
    """A single thought in the reasoning process"""
    id: str
    content: str
    confidence: float = 1.0
    parent_id: Optional[str] = None
    evaluation: Optional[str] = None
    is_refined: bool = False


@dataclass
class Reflection:
    """A reflection on thoughts or actions"""
    reflection_type: ReflectionType
    subject: str
    observations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0


class ReflectiveReasoner:
    """
    Reflective Reasoner
    ====================

    Implements self-reflective reasoning where the agent
    evaluates and improves its own thinking process.
    """

    def __init__(self, model=None):
        self.model = model
        self.thought_history: List[Thought] = []
        self.reflections: List[Reflection] = []
        self.insight_patterns: Dict[str, int] = {}

    async def reason_with_reflection(
        self,
        problem: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Reason with reflection over multiple iterations.

        Args:
            problem: The problem to solve
            max_iterations: Maximum reflection iterations

        Returns:
            Final solution with reflection history
        """
        solution = None
        iterations_data = []

        for iteration in range(max_iterations):
            # Generate initial solution
            thought = await self._generate_thought(problem, iteration)

            # Reflect on the thought
            reflection = await self._reflect(
                thought,
                ReflectionType.DURING_THINKING,
                problem
            )

            # Refine based on reflection
            if reflection.confidence_adjustment < 0.7:
                thought = await self._refine_thought(thought, reflection)
                thought.is_refined = True

            self.thought_history.append(thought)
            iterations_data.append({
                "iteration": iteration + 1,
                "thought": thought.content,
                "reflection": reflection.insights,
                "confidence": thought.confidence
            })

            # Update confidence based on reflection
            thought.confidence *= reflection.confidence_adjustment

            # Check if solution is good enough
            if thought.confidence >= 0.85:
                solution = thought.content
                break

        # Final reflection
        final_reflection = await self._reflect(
            Thought(id="final", content=solution or problem),
            ReflectionType.AFTER_ACTION,
            problem
        )
        self.reflections.append(final_reflection)

        return {
            "solution": solution or "No confident solution found",
            "iterations": iterations_data,
            "final_confidence": thought.confidence if thought else 0.0,
            "reflections": [r.insights for r in self.reflections]
        }

    async def _generate_thought(self, problem: str, iteration: int) -> Thought:
        """Generate a thought about the problem"""
        # In real implementation, this would call the LLM
        thought_content = f"Analysis of '{problem}' - iteration {iteration + 1}"

        return Thought(
            id=f"thought_{iteration}",
            content=thought_content,
            confidence=0.5 + (0.1 * (3 - iteration)),  # Decreasing confidence
            parent_id=None
        )

    async def _reflect(
        self,
        thought: Thought,
        reflection_type: ReflectionType,
        problem: str
    ) -> Reflection:
        """Reflect on a thought or action"""
        observations = []
        insights = []
        improvements = []
        confidence_adj = 1.0

        # Analyze the thought
        if len(thought.content) < 10:
            observations.append("Thought is too brief")
            improvements.append("Provide more detailed reasoning")
            confidence_adj *= 0.8

        # Check for patterns from history
        for prev_thought in self.thought_history[-3:]:
            if thought.content == prev_thought.content:
                observations.append("Similar thought repeated")
                improvements.append("Try a different approach")
                confidence_adj *= 0.7

        # Generate insights
        if confidence_adj > 0.8:
            insights.append("Current approach seems valid")
        else:
            insights.append("Current approach needs adjustment")

        reflection = Reflection(
            reflection_type=reflection_type,
            subject=thought.content,
            observations=observations,
            insights=insights,
            improvements=improvements,
            confidence_adjustment=confidence_adj
        )

        self.reflections.append(reflection)
        return reflection

    async def _refine_thought(self, thought: Thought, reflection: Reflection) -> Thought:
        """Refine a thought based on reflection"""
        refined_content = thought.content

        # Incorporate improvements
        if reflection.improvements:
            refined_content += f"\nRefinement: {', '.join(reflection.improvements)}"

        return Thought(
            id=thought.id + "_refined",
            content=refined_content,
            confidence=thought.confidence,
            parent_id=thought.id,
            evaluation=reflection.insights[0] if reflection.insights else None,
            is_refined=True
        )

    async def analyze_error(self, error: str, context: Dict) -> Reflection:
        """Analyze an error and learn from it"""
        observations = [f"Error occurred: {error}"]
        improvements = []

        # Analyze error patterns
        error_type = context.get("error_type", "unknown")
        if error_type == "timeout":
            improvements.append("Increase timeout duration")
            observations.append("Operation timed out")
        elif error_type == "permission":
            improvements.append("Check permissions before operation")
            observations.append("Permission denied")
        elif error_type == "validation":
            improvements.append("Add input validation")
            observations.append("Input validation failed")

        # Generate insights
        insights = [
            f"Error type: {error_type}",
            f"Context: {list(context.keys())}"
        ]

        reflection = Reflection(
            reflection_type=ReflectionType.ERROR_ANALYSIS,
            subject=error,
            observations=observations,
            insights=insights,
            improvements=improvements,
            confidence_adjustment=0.5
        )

        self.reflections.append(reflection)
        self._update_insight_patterns(insights)
        return reflection

    def _update_insight_patterns(self, insights: List[str]):
        """Update pattern tracking for insights"""
        for insight in insights:
            self.insight_patterns[insight] = self.insight_patterns.get(insight, 0) + 1

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of what has been learned"""
        return {
            "total_reflections": len(self.reflections),
            "total_thoughts": len(self.thought_history),
            "insight_patterns": dict(sorted(
                self.insight_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "reflection_types": {
                rt.value: sum(1 for r in self.reflections if r.reflection_type == rt)
                for rt in ReflectionType
            }
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 59: Reflective Reasoning")
    print("=" * 60)

    reasoner = ReflectiveReasoner()

    # Test with a problem
    problem = "Calculate the sum of all even numbers from 1 to 100"
    result = await reasoner.reason_with_reflection(problem, max_iterations=3)

    print(f"\nProblem: {problem}")
    print(f"\nSolution: {result['solution']}")
    print(f"Confidence: {result['final_confidence']:.2f}")
    print(f"Iterations: {len(result['iterations'])}")

    for i, iteration in enumerate(result['iterations']):
        print(f"\n  Iteration {i+1}:")
        print(f"    Thought: {iteration['thought'][:50]}...")
        print(f"    Reflections: {iteration['reflection']}")
        print(f"    Confidence: {iteration['confidence']:.2f}")

    # Test error analysis
    print("\n" + "=" * 60)
    print("Error Analysis")
    print("=" * 60)

    error_reflection = await reasoner.analyze_error(
        "Permission denied: cannot read file",
        {"error_type": "permission", "file": "/etc/passwd"}
    )

    print(f"\nObservations: {error_reflection.observations}")
    print(f"Insights: {error_reflection.insights}")
    print(f"Improvements: {error_reflection.improvements}")

    # Learning summary
    print("\n" + "=" * 60)
    print("Learning Summary")
    print("=" * 60)
    summary = reasoner.get_learning_summary()
    print(f"Total reflections: {summary['total_reflections']}")
    print(f"Top insight patterns: {summary['insight_patterns']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())