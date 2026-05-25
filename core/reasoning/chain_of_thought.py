"""Chain-of-Thought Reasoning Engine - Day 7 Implementation.

Provides step-by-step reasoning capabilities with multiple reasoning strategies:
- Standard Chain-of-Thought (CoT)
- Tree of Thoughts (ToT)
- ReAct (Reason + Act)
- Reflexion
"""

import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning strategies."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT = "react"
    REFLEXION = "reflexion"


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""
    step_id: str
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    reasoning_type: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT
    confidence: float = 1.0
    parent_step_id: Optional[str] = None
    children_step_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    is_final: bool = False


@dataclass
class ReasoningResult:
    """Result of reasoning process."""
    reasoning_id: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep]
    final_answer: Optional[str] = None
    confidence: float = 0.0
    reasoning_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ChainOfThought:
    """
    Chain-of-Thought reasoning engine with multiple strategies.
    """

    def __init__(
        self,
        max_steps: int = 10,
        max_depth: int = 5,
        timeout_seconds: int = 30,
        llm_provider: Optional[Callable] = None
    ):
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.timeout_seconds = timeout_seconds
        self.llm_provider = llm_provider
        self._reasoning_cache: Dict[str, ReasoningResult] = {}

    def set_llm_provider(self, provider: Callable):
        """Set the LLM provider for reasoning."""
        self.llm_provider = provider

    async def reason(
        self,
        problem: str,
        reasoning_type: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ReasoningResult:
        """
        Execute reasoning process on a problem.

        Args:
            problem: The problem to reason about
            reasoning_type: Type of reasoning strategy to use
            context: Additional context for reasoning
            tools: Available tools for ReAct reasoning

        Returns:
            ReasoningResult with complete reasoning trace
        """
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        context = context or {}
        tools = tools or []

        logger.info(f"Starting {reasoning_type} reasoning: {reasoning_id}")

        try:
            if reasoning_type == ReasoningType.CHAIN_OF_THOUGHT:
                result = await self._chain_of_thought(problem, context)
            elif reasoning_type == ReasoningType.TREE_OF_THOUGHTS:
                result = await self._tree_of_thoughts(problem, context)
            elif reasoning_type == ReasoningType.REACT:
                result = await self._react_reasoning(problem, context, tools)
            elif reasoning_type == ReasoningType.REFLEXION:
                result = await self._reflexion_reasoning(problem, context)
            else:
                result = await self._chain_of_thought(problem, context)

            result.completed_at = datetime.now()
            self._reasoning_cache[reasoning_id] = result
            return result

        except Exception as e:
            logger.exception(f"Reasoning failed: {reasoning_id}")
            return ReasoningResult(
                reasoning_id=reasoning_id,
                reasoning_type=reasoning_type,
                steps=[],
                error=str(e)
            )

    async def _chain_of_thought(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> ReasoningResult:
        """Standard Chain-of-Thought reasoning."""
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        steps: List[ReasoningStep] = []

        # Generate initial thought
        thought = self._generate_initial_thought(problem, context)
        step = ReasoningStep(
            step_id=f"step_{len(steps)}",
            thought=thought,
            reasoning_type=ReasoningType.CHAIN_OF_THOUGHT
        )
        steps.append(step)

        # Generate reasoning steps
        current_step = step
        for i in range(1, self.max_steps):
            # If we have an LLM provider, use it
            if self.llm_provider:
                next_thought = await self.llm_provider({
                    "prompt": self._build_cot_prompt(problem, steps, context),
                    "context": context
                })
            else:
                # Generate simple reasoning step
                next_thought = self._generate_reasoning_step(problem, steps, context)

            if not next_thought:
                break

            next_step = ReasoningStep(
                step_id=f"step_{i}",
                thought=next_thought,
                parent_step_id=current_step.step_id,
                reasoning_type=ReasoningType.CHAIN_OF_THOUGHT
            )
            current_step.children_step_ids.append(next_step.step_id)
            steps.append(next_step)
            current_step = next_step

            # Check if we've reached a conclusion
            if self._is_conclusion(next_thought):
                current_step.is_final = True
                break

        # Extract final answer
        final_answer = self._extract_final_answer(steps)
        confidence = self._calculate_confidence(steps)

        return ReasoningResult(
            reasoning_id=reasoning_id,
            reasoning_type=ReasoningType.CHAIN_OF_THOUGHT,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            reasoning_path=[s.step_id for s in steps]
        )

    async def _tree_of_thoughts(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> ReasoningResult:
        """Tree of Thoughts reasoning - explores multiple branches."""
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        steps: List[ReasoningStep] = []

        # Generate initial thoughts (root nodes)
        initial_thoughts = self._generate_initial_thoughts(problem, context, n=3)
        root_steps = []

        for i, thought in enumerate(initial_thoughts):
            step = ReasoningStep(
                step_id=f"step_0_{i}",
                thought=thought,
                reasoning_type=ReasoningType.TREE_OF_THOUGHTS
            )
            steps.append(step)
            root_steps.append(step)

        # Explore each branch
        all_branches = []
        for root in root_steps:
            branch = await self._explore_branch(root, problem, context, depth=1)
            all_branches.append(branch)
            steps.extend(branch)

        # Select best branch based on confidence
        best_branch = max(all_branches, key=lambda b: self._calculate_confidence(b))
        final_answer = self._extract_final_answer(best_branch)

        return ReasoningResult(
            reasoning_id=reasoning_id,
            reasoning_type=ReasoningType.TREE_OF_THOUGHTS,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(best_branch),
            reasoning_path=[s.step_id for s in best_branch]
        )

    async def _react_reasoning(
        self,
        problem: str,
        context: Dict[str, Any],
        tools: List[Dict[str, Any]]
    ) -> ReasoningResult:
        """ReAct (Reason + Act) reasoning with tool use."""
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        steps: List[ReasoningStep] = []

        # Initial thought
        thought = f"Problem: {problem}"
        step = ReasoningStep(
            step_id="step_0",
            thought=thought,
            reasoning_type=ReasoningType.REACT
        )
        steps.append(step)
        current_step = step

        # ReAct loop
        for i in range(1, self.max_steps):
            # Reason about what action to take
            action = self._select_action(problem, steps, tools)

            if not action:
                break

            # Execute action
            observation = await self._execute_action(action, tools)

            # Create reasoning step
            step = ReasoningStep(
                step_id=f"step_{i}",
                thought=f"Action: {action}",
                action=action,
                observation=observation,
                parent_step_id=current_step.step_id,
                reasoning_type=ReasoningType.REACT
            )
            current_step.children_step_ids.append(step.step_id)
            steps.append(step)
            current_step = step

            # Check if we've reached a conclusion
            if self._is_conclusion(observation or ""):
                current_step.is_final = True
                break

        final_answer = self._extract_final_answer(steps)
        return ReasoningResult(
            reasoning_id=reasoning_id,
            reasoning_type=ReasoningType.REACT,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(steps),
            reasoning_path=[s.step_id for s in steps]
        )

    async def _reflexion_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> ReasoningResult:
        """Reflexion reasoning with self-reflection."""
        reasoning_id = f"reason_{uuid.uuid4().hex[:12]}"
        steps: List[ReasoningStep] = []

        # Initial solution attempt
        initial_steps = await self._chain_of_thought(problem, context)
        steps.extend(initial_steps.steps)

        # Reflexion loop
        for iteration in range(3):
            # Reflect on the solution
            reflection = await self._reflect(initial_steps, context)

            reflection_step = ReasoningStep(
                step_id=f"reflection_{iteration}",
                thought=f"Reflection: {reflection}",
                reasoning_type=ReasoningType.REFLEXION,
                parent_step_id=steps[-1].step_id if steps else None
            )
            steps.append(reflection_step)

            # If reflection suggests improvement needed, continue
            if not self._needs_improvement(reflection):
                break

        final_answer = self._extract_final_answer(steps)
        return ReasoningResult(
            reasoning_id=reasoning_id,
            reasoning_type=ReasoningType.REFLEXION,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(steps),
            reasoning_path=[s.step_id for s in steps]
        )

    async def _explore_branch(
        self,
        root: ReasoningStep,
        problem: str,
        context: Dict[str, Any],
        depth: int
    ) -> List[ReasoningStep]:
        """Explore a branch in Tree of Thoughts."""
        if depth >= self.max_depth:
            return [root]

        branch = [root]

        # Generate next thoughts
        next_thoughts = self._generate_reasoning_step(problem, branch, context, n=2)

        for thought in next_thoughts:
            step = ReasoningStep(
                step_id=f"step_{depth}_{len(branch)}",
                thought=thought,
                parent_step_id=root.step_id,
                reasoning_type=ReasoningType.TREE_OF_THOUGHTS
            )
            root.children_step_ids.append(step.step_id)

            # Recursively explore
            sub_branch = await self._explore_branch(step, problem, context, depth + 1)
            branch.extend(sub_branch)

        return branch

    # --- Helper methods ---

    def _generate_initial_thought(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate initial thought for the problem."""
        return f"Let me break down this problem: {problem}"

    def _generate_initial_thoughts(
        self,
        problem: str,
        context: Dict[str, Any],
        n: int
    ) -> List[str]:
        """Generate multiple initial thoughts for ToT."""
        base_thoughts = [
            f"Approach 1: {problem}",
            f"Approach 2: {problem}",
            f"Approach 3: {problem}"
        ]
        return base_thoughts[:n]

    def _generate_reasoning_step(
        self,
        problem: str,
        steps: List[ReasoningStep],
        context: Dict[str, Any],
        n: int = 1
    ) -> List[str]:
        """Generate next reasoning step(s)."""
        if steps:
            last_thought = steps[-1].thought
            return [f"Building on previous thought: {last_thought[:50]}..."]
        return [f"Next step in reasoning about: {problem}"]

    def _build_cot_prompt(
        self,
        problem: str,
        steps: List[ReasoningStep],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for Chain-of-Thought reasoning."""
        history = "\n".join([f"Step {i+1}: {s.thought}" for i, s in enumerate(steps)])
        return f"""Problem: {problem}

Previous reasoning:
{history}

Continue the reasoning step by step. Provide your next thought."""

    def _is_conclusion(self, thought: str) -> bool:
        """Check if the thought indicates a conclusion."""
        conclusion_indicators = [
            "therefore", "conclusion", "final answer",
            "in summary", "finally", "answer is"
        ]
        return any(indicator in thought.lower() for indicator in conclusion_indicators)

    def _extract_final_answer(self, steps: List[ReasoningStep]) -> Optional[str]:
        """Extract final answer from reasoning steps."""
        if not steps:
            return None

        # Find the final step
        for step in reversed(steps):
            if step.is_final or self._is_conclusion(step.thought):
                return step.observation or step.thought

        return steps[-1].thought if steps else None

    def _calculate_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate confidence score for reasoning."""
        if not steps:
            return 0.0

        # Base confidence on number of steps and their confidence
        step_confidence = sum(s.confidence for s in steps) / len(steps)
        length_factor = min(len(steps) / self.max_steps, 1.0)

        return (step_confidence * 0.7) + (length_factor * 0.3)

    def _select_action(
        self,
        problem: str,
        steps: List[ReasoningStep],
        tools: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Select next action based on problem and available tools."""
        if not tools:
            return None
        return tools[0].get("name", "default_tool")

    async def _execute_action(
        self,
        action: str,
        tools: List[Dict[str, Any]]
    ) -> str:
        """Execute action and return observation."""
        # Find the tool
        tool = next((t for t in tools if t.get("name") == action), None)
        if tool and "execute" in tool:
            try:
                result = await tool["execute"]()
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        return f"Executed: {action}"

    async def _reflect(
        self,
        reasoning_result: ReasoningResult,
        context: Dict[str, Any]
    ) -> str:
        """Generate reflection on reasoning result."""
        return f"Reviewing reasoning with {len(reasoning_result.steps)} steps. " \
               f"Confidence: {reasoning_result.confidence:.2f}"

    def _needs_improvement(self, reflection: str) -> bool:
        """Check if reflection suggests improvement is needed."""
        improvement_indicators = ["improve", "better", "incorrect", "error", "retry"]
        return any(indicator in reflection.lower() for indicator in improvement_indicators)

    def get_reasoning(self, reasoning_id: str) -> Optional[ReasoningResult]:
        """Get cached reasoning result."""
        return self._reasoning_cache.get(reasoning_id)

    def clear_cache(self):
        """Clear reasoning cache."""
        self._reasoning_cache.clear()


# Global reasoning engine instance
_reasoning_engine: Optional[ChainOfThought] = None


def get_reasoning_engine() -> ChainOfThought:
    """Get the global reasoning engine instance."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ChainOfThought()
    return _reasoning_engine