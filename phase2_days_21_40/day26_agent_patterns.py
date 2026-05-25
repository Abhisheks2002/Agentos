"""
Day 26: Agent Patterns - Design Patterns for AI Agents
=======================================================
Skill: Agent Design Patterns
Mini Project: Pattern Library

Common patterns for building robust AI agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class ReflectionStrategy(str, Enum):
    """How agent reflects on its work"""
    NONE = "none"
    AFTER_EACH_STEP = "after_each_step"
    AFTER_ALL_STEPS = "after_all_steps"
    ON_ERROR = "on_error"


class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent
    =================================

    Pattern: Think, Act, Observe cycle
    """

    def __init__(self, name: str, tools: List[Callable] = None):
        self.name = name
        self.tools = tools or []
        self.max_iterations = 5

    async def run(self, task: str) -> Dict[str, Any]:
        """Execute task using ReAct pattern"""
        steps = []
        context = task

        for i in range(self.max_iterations):
            # Thought
            thought = f"Step {i+1}: Analyzing task..."

            # Action
            action = self._select_action(context)
            observation = await self._execute_action(action, context)

            # Record step
            steps.append({
                "step": i + 1,
                "thought": thought,
                "action": action,
                "observation": observation
            })

            # Check if done
            if self._is_complete(observation):
                break

            # Update context
            context = observation

        return {
            "task": task,
            "steps": steps,
            "final_result": steps[-1]["observation"] if steps else None
        }

    def _select_action(self, context: str) -> str:
        """Select next action"""
        return "think"  # Simplified

    async def _execute_action(self, action: str, context: str) -> str:
        """Execute action"""
        await asyncio.sleep(0.1)
        return f"Result of {action}"

    def _is_complete(self, observation: str) -> bool:
        """Check if task is complete"""
        return len(observation) > 10


class ReflexionAgent:
    """
    Reflexion Agent
    ===============

    Pattern: Reflect on failures and improve
    """

    def __init__(self, name: str):
        self.name = name
        self.memory: List[Dict[str, Any]] = []

    async def run(self, task: str, max_attempts: int = 3) -> Dict[str, Any]:
        """Run with reflection on failures"""
        attempts = []
        success = False

        for attempt in range(max_attempts):
            # Get context from previous attempts
            context = self._build_context(attempts)

            # Execute
            result = await self._execute(task, context)
            attempts.append(result)

            # Reflect
            if not result.get("success"):
                reflection = await self._reflect(result, attempts)
                result["reflection"] = reflection
                self.memory.append(reflection)
            else:
                success = True
                break

        return {
            "task": task,
            "attempts": attempts,
            "success": success,
            "reflections": self.memory
        }

    def _build_context(self, attempts: List[Dict]) -> str:
        """Build context from previous attempts"""
        if not attempts:
            return ""

        reflections = [a.get("reflection", "") for a in attempts if a.get("reflection")]
        return " | ".join(reflections)

    async def _execute(self, task: str, context: str) -> Dict[str, Any]:
        """Execute task (simplified)"""
        await asyncio.sleep(0.1)

        # Simulate random success
        import random
        success = random.random() > 0.5

        return {
            "success": success,
            "result": f"Attempt result for: {task}",
            "context": context
        }

    async def _reflect(self, result: Dict, attempts: List[Dict]) -> Dict[str, Any]:
        """Reflect on attempt"""
        return {
            "attempt_number": len(attempts),
            "what_went_wrong": "Need more context",
            "improvement": "Add more details",
            "timestamp": datetime.now().isoformat()
        }


class PlanExecuteAgent:
    """
    Plan-and-Execute Agent
    ======================

    Pattern: Plan first, then execute
    """

    def __init__(self, name: str):
        self.name = name

    async def run(self, task: str) -> Dict[str, Any]:
        """Plan and execute"""
        # Plan
        plan = await self._plan(task)

        # Execute
        results = []
        for step in plan["steps"]:
            result = await self._execute_step(step)
            results.append(result)

            if not result["success"]:
                break

        return {
            "task": task,
            "plan": plan,
            "results": results,
            "success": all(r["success"] for r in results)
        }

    async def _plan(self, task: str) -> Dict[str, Any]:
        """Create plan"""
        # Simple plan generation
        num_steps = min(3, max(1, len(task) // 10))

        return {
            "task": task,
            "steps": [
                {"id": i + 1, "description": f"Step {i+1}"}
                for i in range(num_steps)
            ]
        }

    async def _execute_step(self, step: Dict) -> Dict[str, Any]:
        """Execute single step"""
        await asyncio.sleep(0.1)

        return {
            "step_id": step["id"],
            "success": True,
            "result": f"Completed: {step['description']}"
        }


class ToolUseAgent:
    """
    Tool-Use Agent with structured output
    ======================================

    Pattern: Use tools based on structured output
    """

    def __init__(self, name: str):
        self.name = name
        self.tools = {}

    def register_tool(self, name: str, handler: Callable):
        """Register a tool"""
        self.tools[name] = handler

    async def run(self, task: str) -> Dict[str, Any]:
        """Run with tool use"""
        # Get tool call from LLM (simulated)
        tool_calls = self._parse_tool_calls(task)

        results = []
        for call in tool_calls:
            if call["name"] in self.tools:
                result = await self.tools[call["name"]](**call["params"])
                results.append({
                    "tool": call["name"],
                    "result": result
                })

        return {
            "task": task,
            "tool_calls": tool_calls,
            "results": results
        }

    def _parse_tool_calls(self, task: str) -> List[Dict[str, Any]]:
        """Parse tool calls from task (simplified)"""
        calls = []

        if "search" in task.lower():
            calls.append({"name": "search", "params": {"query": task}})

        if "calculate" in task.lower():
            calls.append({"name": "calculate", "params": {"expression": "2+2"}})

        return calls


class SelfCriticAgent:
    """
    Self-Critic Agent
    ==================

    Pattern: Criticize and improve own responses
    """

    def __init__(self, name: str):
        self.name = name

    async def run(self, task: str) -> Dict[str, Any]:
        """Run with self-critique"""
        # Generate initial response
        response = await self._generate(task)

        # Critique
        critique = await self._critique(response, task)

        # Improve if needed
        if critique["needs_improvement"]:
            improved = await self._improve(response, critique)
            response = improved

        return {
            "task": task,
            "initial_response": response,
            "critique": critique,
            "final_response": response if not critique["needs_improvement"] else improved
        }

    async def _generate(self, task: str) -> str:
        """Generate response"""
        return f"Generated response for: {task}"

    async def _critique(self, response: str, task: str) -> Dict[str, Any]:
        """Critique response"""
        # Simple critique
        needs_improvement = len(response) < 20

        return {
            "needs_improvement": needs_improvement,
            "issues": ["Too brief"] if needs_improvement else [],
            "suggestions": ["Add more detail"] if needs_improvement else []
        }

    async def _improve(self, response: str, critique: Dict) -> str:
        """Improve response"""
        return response + " [Improved]"


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Patterns Demo")
    print("=" * 70)

    import asyncio

    # ReAct Agent
    print("\n[1] ReAct Agent")
    print("-" * 40)

    react = ReActAgent("ReActBot")
    result = asyncio.run(react.run("Analyze this task"))
    print(f"  Steps: {len(result['steps'])}")
    print(f"  Complete: {result['final_result'] is not None}")

    # Reflexion Agent
    print("\n[2] Reflexion Agent")
    print("-" * 40)

    reflexion = ReflexionAgent("ReflexionBot")
    result = asyncio.run(reflexion.run("Complex task", max_attempts=3))
    print(f"  Attempts: {len(result['attempts'])}")
    print(f"  Success: {result['success']}")

    # Plan-Execute Agent
    print("\n[3] Plan-Execute Agent")
    print("-" * 40)

    planner = PlanExecuteAgent("PlannerBot")
    result = asyncio.run(planner.run("Build something"))
    print(f"  Plan steps: {len(result['plan']['steps'])}")
    print(f"  Success: {result['success']}")

    # Tool-Use Agent
    print("\n[4] Tool-Use Agent")
    print("-" * 40)

    tool_agent = ToolUseAgent("ToolBot")
    tool_agent.register_tool("search", lambda q: f"Results for: {q}")
    result = asyncio.run(tool_agent.run("Search for AI"))
    print(f"  Tool calls: {len(result['tool_calls'])}")

    # Self-Critic Agent
    print("\n[5] Self-Critic Agent")
    print("-" * 40)

    critic = SelfCriticAgent("CriticBot")
    result = asyncio.run(critic.run("Explain something"))
    print(f"  Needs improvement: {result['critique']['needs_improvement']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()