"""
Day 59: Auto-Regressive Agents
===============================

Auto-regressive agent behavior with self-correction and iterative refinement.

Key Concepts:
- Self-correction loops
- Iterative refinement
- Error recovery
- Adaptive behavior
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    CORRECTING = "correcting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Thought:
    """A single thought in the agent's reasoning chain"""
    id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5
    parent_id: str = None


@dataclass
class ActionResult:
    """Result of an action execution"""
    action_type: str
    params: Dict[str, Any]
    result: Any
    success: bool
    error: str = None
    execution_time: float = 0.0


@dataclass
class Iteration:
    """One iteration of the agent loop"""
    iteration: int
    thought: str
    action: str
    action_params: Dict[str, Any]
    result: ActionResult
    feedback: str = ""
    corrected: bool = False


class AutoRegressiveAgent:
    """
    Auto-Regressive Agent
    =====================

    An agent that iteratively refines its responses through
    self-correction and feedback loops.
    """

    def __init__(
        self,
        name: str,
        max_iterations: int = 5,
        confidence_threshold: float = 0.8,
        correction_enabled: bool = True
    ):
        self.name = name
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.correction_enabled = correction_enabled

        self.state = AgentState.IDLE
        self.iterations: List[Iteration] = []
        self.thought_chain: List[Thought] = []

        # Callbacks
        self.on_think: Optional[Callable] = None
        self.on_act: Optional[Callable] = None
        self.on_correct: Optional[Callable] = None

    def _create_thought(self, content: str, parent_id: str = None) -> Thought:
        """Create a new thought"""
        return Thought(
            id=f"thought_{len(self.thought_chain)}_{random.randint(1000, 9999)}",
            content=content,
            parent_id=parent_id
        )

    async def think(self, context: Dict[str, Any]) -> str:
        """Generate the next thought based on context"""
        # Simulate thinking
        if self.on_think:
            return await self.on_think(context)

        # Simple rule-based thinking
        if not self.iterations:
            return f"Analyzing the task: {context.get('task', 'unknown')}"
        else:
            last = self.iterations[-1]
            if not last.result.success:
                return f"Analyzing error: {last.result.error}"
            return f"Reviewing result: {last.result.result}"

    async def act(self, thought: str, context: Dict[str, Any]) -> ActionResult:
        """Execute an action based on thought"""
        if self.on_act:
            return await self.on_act(thought, context)

        # Simulate action execution
        action_type = context.get("action_type", "respond")
        return ActionResult(
            action_type=action_type,
            params={},
            result=f"Action completed: {thought[:50]}",
            success=True
        )

    def evaluate_result(
        self,
        result: ActionResult,
        expected: Any = None
    ) -> tuple[bool, str]:
        """Evaluate if the result is satisfactory"""
        if not result.success:
            return False, f"Action failed: {result.error}"

        # Simple evaluation
        if expected and result.result != expected:
            return False, f"Result does not match expected: {expected}"

        return True, "Result acceptable"

    async def correct(
        self,
        iteration: Iteration,
        feedback: str
    ) -> str:
        """Generate a correction based on feedback"""
        if self.on_correct:
            return await self.on_correct(iteration, feedback)

        # Generate correction thought
        correction = f"Correction needed: {feedback}"
        return correction

    async def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the auto-regressive agent

        The agent loop:
        1. Think about the current state
        2. Act based on thought
        3. Evaluate result
        4. If unsatisfactory and can correct, go to step 1 with correction
        5. Otherwise, return result
        """
        context = context or {}
        context["task"] = task
        self.state = AgentState.THINKING
        self.iterations = []
        self.thought_chain = []

        for i in range(self.max_iterations):
            iteration_num = i + 1

            # Step 1: Think
            self.state = AgentState.THINKING
            thought = await self.think(context)

            # Store thought
            thought_obj = self._create_thought(thought)
            if self.thought_chain:
                thought_obj.parent_id = self.thought_chain[-1].id
            self.thought_chain.append(thought_obj)

            # Step 2: Act
            self.state = AgentState.ACTING
            action_result = await self.act(thought, context)

            # Step 3: Evaluate
            expected = context.get("expected_result")
            is_satisfactory, feedback = self.evaluate_result(
                action_result,
                expected
            )

            # Store iteration
            iteration = Iteration(
                iteration=iteration_num,
                thought=thought,
                action=action_result.action_type,
                action_params=action_result.params,
                result=action_result,
                feedback=feedback
            )
            self.iterations.append(iteration)

            # Step 4: Check if we need to correct
            if is_satisfactory:
                self.state = AgentState.COMPLETED
                return {
                    "success": True,
                    "result": action_result.result,
                    "iterations": len(self.iterations),
                    "thought_chain": [
                        t.content for t in self.thought_chain
                    ]
                }

            # Need correction
            if self.correction_enabled and iteration_num < self.max_iterations:
                self.state = AgentState.CORRECTING
                correction = await self.correct(iteration, feedback)
                context["correction"] = correction
                context["previous_result"] = action_result.result
                iteration.corrected = True
            else:
                self.state = AgentState.FAILED
                return {
                    "success": False,
                    "error": "Max iterations reached without satisfactory result",
                    "iterations": self.iterations,
                    "last_feedback": feedback
                }

        self.state = AgentState.FAILED
        return {
            "success": False,
            "error": "Max iterations reached",
            "iterations": self.iterations
        }

    def get_thought_tree(self) -> Dict:
        """Get the thought chain as a tree structure"""
        tree = []
        for thought in self.thought_chain:
            node = {
                "id": thought.id,
                "content": thought.content,
                "timestamp": thought.timestamp.isoformat(),
                "confidence": thought.confidence,
                "children": []
            }

            if thought.parent_id:
                for t in tree:
                    if t["id"] == thought.parent_id:
                        t["children"].append(node)
                        break
            else:
                tree.append(node)

        return tree


class ReActAgent(AutoRegressiveAgent):
    """
    ReAct Agent (Reasoning + Acting)
    =================================

    Combines reasoning and acting in a single loop.
    """

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        """Register a tool for the agent to use"""
        self.tools[name] = func

    async def think(self, context: Dict[str, Any]) -> str:
        """Think about which action to take"""
        task = context.get("task", "")
        available_tools = list(self.tools.keys())

        # Simple tool selection
        if "search" in task.lower() and "search" in available_tools:
            return "I should search for information"
        elif "calculate" in task.lower() and "calculator" in available_tools:
            return "I should use the calculator"
        else:
            return "I should respond directly"

    async def act(self, thought: str, context: Dict[str, Any]) -> ActionResult:
        """Execute action based on thought"""
        import time
        start = time.time()

        # Determine tool to use
        if "search" in thought.lower() and "search" in self.tools:
            result = await self.tools["search"](context.get("query", ""))
            action_type = "search"
        elif "calculator" in thought.lower() and "calculator" in self.tools:
            result = self.tools["calculator"](context.get("expression", "0"))
            action_type = "calculator"
        else:
            result = f"Processing: {context.get('task', '')}"
            action_type = "respond"

        return ActionResult(
            action_type=action_type,
            params=context,
            result=result,
            success=True,
            execution_time=time.time() - start
        )


# Demo
async def main():
    print("=" * 60)
    print("Day 59: Auto-Regressive Agents")
    print("=" * 60)

    # Create basic autoregressive agent
    agent = AutoRegressiveAgent(
        name="ResearchAgent",
        max_iterations=3,
        confidence_threshold=0.7
    )

    # Run task
    result = await agent.run(
        task="Find information about quantum computing",
        context={"action_type": "search"}
    )

    print(f"\nResult: {result}")

    # Create ReAct agent
    react_agent = ReActAgent(name="Assistant")

    # Register tools
    def search_tool(query: str) -> str:
        return f"Search results for: {query}"

    def calculator(expr: str) -> str:
        try:
            return str(eval(expr))
        except:
            return "Error"

    react_agent.register_tool("search", search_tool)
    react_agent.register_tool("calculator", calculator)

    # Run with tools
    result2 = await react_agent.run(
        task="Calculate 2 + 2",
        context={"action_type": "calculator", "expression": "2+2"}
    )

    print(f"\nReAct Result: {result2}")

    print("\n" + "=" * 60)
    print("Auto-regressive agent demonstration complete")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())