"""
Day 39: Reflection and Planning
===============================
Skill: Meta-Cognition
Mini Project: ReAct Agent

Building agents that can reflect and plan.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import deque


class ActionType(str, Enum):
    """Types of actions an agent can take"""
    THINK = "think"
    OBSERVE = "observe"
    PLAN = "plan"
    EXECUTE = "execute"
    REFLECT = "reflect"
    ANSWER = "answer"


@dataclass
class Thought:
    """A thought or action"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.THINK
    content: str = ""
    reasoning: str = ""
    result: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0


class ReActAgent:
    """Reasoning + Acting Agent"""

    def __init__(
        self,
        name: str,
        tools: Dict[str, Callable] = None,
        max_iterations: int = 10
    ):
        self.name = name
        self.tools = tools or {}
        self.max_iterations = max_iterations
        self.thought_history: List[Thought] = []

    async def think(self, prompt: str) -> str:
        """Think about a problem"""
        thought = Thought(
            action_type=ActionType.THINK,
            content=prompt,
            reasoning="Analyzing the problem"
        )
        self.thought_history.append(thought)

        # Simulate reasoning
        await asyncio.sleep(0.1)

        # Simple reasoning simulation
        if "calculate" in prompt.lower() or "sum" in prompt.lower():
            result = "I need to perform a calculation"
        elif "search" in prompt.lower() or "find" in prompt.lower():
            result = "I need to search for information"
        elif "what" in prompt.lower() or "who" in prompt.lower():
            result = "I need to answer based on my knowledge"
        else:
            result = "Let me break this down"

        thought.result = result
        return result

    async def observe(self, observation: str) -> str:
        """Observe and process information"""
        thought = Thought(
            action_type=ActionType.OBSERVE,
            content=observation,
            reasoning="Processing observation"
        )
        self.thought_history.append(thought)

        await asyncio.sleep(0.05)
        thought.result = f"Observed: {observation[:50]}..."
        return thought.result

    async def plan(self, goal: str, steps: List[str] = None) -> List[str]:
        """Create a plan"""
        thought = Thought(
            action_type=ActionType.PLAN,
            content=goal,
            reasoning="Creating action plan"
        )
        self.thought_history.append(thought)

        # Generate plan steps if not provided
        if not steps:
            steps = [
                f"Understand the goal: {goal}",
                "Break down into smaller tasks",
                "Execute each task",
                "Verify the result"
            ]

        thought.result = steps
        return steps

    async def execute(self, action: str, **kwargs) -> Any:
        """Execute an action or tool"""
        thought = Thought(
            action_type=ActionType.EXECUTE,
            content=action,
            reasoning=f"Executing: {action}"
        )
        self.thought_history.append(thought)

        # Check if it's a tool
        if action in self.tools:
            result = await self.tools[action](**kwargs)
        else:
            # Simulate execution
            await asyncio.sleep(0.2)
            result = f"Executed: {action}"

        thought.result = result
        return result

    async def reflect(self) -> Dict[str, Any]:
        """Reflect on recent actions"""
        thought = Thought(
            action_type=ActionType.REFLECT,
            content="Reflection",
            reasoning="Analyzing recent thought history"
        )
        self.thought_history.append(thought)

        # Analyze recent thoughts
        recent = self.thought_history[-5:]
        actions = [t.action_type.value for t in recent]

        reflection = {
            "actions_taken": actions,
            "total_thoughts": len(self.thought_history),
            "last_action": recent[-1].content if recent else None,
            "success_rate": 0.85  # Simplified
        }

        thought.result = reflection
        return reflection

    async def answer(self, question: str) -> str:
        """Answer a question"""
        thought = Thought(
            action_type=ActionType.ANSWER,
            content=question,
            reasoning="Generating answer"
        )
        self.thought_history.append(thought)

        # Simple answer generation
        await asyncio.sleep(0.1)

        if "hello" in question.lower() or "hi" in question.lower():
            answer = "Hello! How can I help you today?"
        elif "name" in question.lower():
            answer = f"I am {self.name}, an AI agent."
        elif "your" in question.lower():
            answer = "I am an AI agent built with the ReAct framework."
        else:
            answer = "That's an interesting question. Let me think..."

        thought.result = answer
        return answer

    async def run(self, query: str) -> str:
        """Run the ReAct loop"""
        # 1. Think
        await self.think(query)

        # 2. Observe
        await self.observe(f"Received query: {query}")

        # 3. Plan
        steps = await self.plan(query)

        # 4. Execute steps
        for step in steps:
            await self.execute(step)

        # 5. Reflect
        reflection = await self.reflect()

        # 6. Answer
        answer = await self.answer(query)
        return answer


class PlanningAgent:
    """Agent with advanced planning capabilities"""

    def __init__(self, name: str):
        self.name = name
        self.goals: List[Dict] = []
        self.plans: Dict[str, List[str]] = {}

    def create_goal(self, description: str, priority: int = 5) -> Dict:
        """Create a new goal"""
        goal = {
            "id": str(uuid.uuid4()),
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "subgoals": []
        }
        self.goals.append(goal)
        return goal

    def decompose_goal(self, goal_id: str) -> List[str]:
        """Decompose a goal into subgoals"""
        goal = next((g for g in self.goals if g["id"] == goal_id), None)
        if not goal:
            return []

        # Simple decomposition
        subgoals = [
            f"Analyze: {goal['description']}",
            f"Plan: {goal['description']}",
            f"Execute: {goal['description']}",
            f"Verify: {goal['description']}"
        ]

        goal["subgoals"] = subgoals
        return subgoals

    def create_plan(self, goal: str, constraints: Dict = None) -> List[Dict]:
        """Create a detailed plan"""
        plan_steps = []

        # Create plan with backtracking potential
        steps = [
            {
                "id": "1",
                "action": "analyze",
                "description": f"Analyze {goal}",
                "dependencies": [],
                "estimated_time": 1
            },
            {
                "id": "2",
                "action": "research",
                "description": f"Research {goal}",
                "dependencies": ["1"],
                "estimated_time": 2
            },
            {
                "id": "3",
                "action": "execute",
                "description": f"Execute solution for {goal}",
                "dependencies": ["2"],
                "estimated_time": 3
            },
            {
                "id": "4",
                "action": "verify",
                "description": f"Verify results for {goal}",
                "dependencies": ["3"],
                "estimated_time": 1
            }
        ]

        plan_id = str(uuid.uuid4())
        self.plans[plan_id] = steps

        return steps

    def get_plan_status(self, plan_id: str) -> Dict:
        """Get plan execution status"""
        if plan_id not in self.plans:
            return {"error": "Plan not found"}

        steps = self.plans[plan_id]
        return {
            "plan_id": plan_id,
            "total_steps": len(steps),
            "completed": sum(1 for s in steps if s.get("status") == "completed"),
            "pending": sum(1 for s in steps if s.get("status") != "completed"),
            "status": "completed" if all(s.get("status") == "completed" for s in steps) else "in_progress"
        }

    def adjust_plan(self, plan_id: str, feedback: str) -> List[Dict]:
        """Adjust plan based on feedback"""
        if plan_id not in self.plans:
            return []

        # Simple adjustment: add verification step
        steps = self.plans[plan_id]

        # Check if feedback indicates failure
        if "fail" in feedback.lower() or "error" in feedback.lower():
            # Add retry step
            steps.append({
                "id": str(len(steps) + 1),
                "action": "retry",
                "description": "Retry with adjusted approach",
                "dependencies": [steps[-1]["id"]],
                "estimated_time": 2
            })

        return steps


class ReflectionAgent:
    """Agent with reflection capabilities"""

    def __init__(self, name: str):
        self.name = name
        self.experiences: List[Dict] = []
        self.lessons: List[str] = []
        self.performance_history: List[Dict] = []

    def record_experience(self, action: str, result: Any, context: Dict = None):
        """Record an experience"""
        experience = {
            "id": str(uuid.uuid4()),
            "action": action,
            "result": result,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "success": result is not None
        }
        self.experiences.append(experience)
        return experience

    def reflect_on_experiences(self, count: int = 5) -> List[str]:
        """Reflect on recent experiences"""
        recent = self.experiences[-count:]
        lessons = []

        for exp in recent:
            if exp["success"]:
                lessons.append(f"Success: {exp['action']} worked well")
            else:
                lessons.append(f"Learning: {exp['action']} needs improvement")

        self.lessons.extend(lessons)
        return lessons

    def analyze_performance(self) -> Dict:
        """Analyze agent performance"""
        total = len(self.experiences)
        if total == 0:
            return {"total": 0, "success_rate": 0}

        successful = sum(1 for e in self.experiences if e["success"])
        success_rate = successful / total

        return {
            "total_experiences": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": success_rate,
            "lessons_learned": len(self.lessons)
        }

    def extract_lessons(self) -> List[str]:
        """Extract general lessons from experiences"""
        # Group by action type
        action_results: Dict[str, List[bool]] = {}

        for exp in self.experiences:
            action = exp["action"]
            if action not in action_results:
                action_results[action] = []
            action_results[action].append(exp["success"])

        lessons = []
        for action, results in action_results.items():
            success_rate = sum(results) / len(results)
            if success_rate < 0.5:
                lessons.append(f"Need to improve: {action} (success rate: {success_rate:.0%})")
            else:
                lessons.append(f"Good at: {action} (success rate: {success_rate:.0%})")

        return lessons


# Demo
def run_demo():
    print("=" * 70)
    print("Reflection and Planning Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Test ReAct Agent
        print("\n[1] ReAct Agent")
        print("-" * 40)

        def calculator(expression: str) -> str:
            """Simple calculator tool"""
            try:
                result = eval(expression)
                return str(result)
            except:
                return "Error"

        tools = {"calculator": calculator}
        agent = ReActAgent("Assistant", tools)

        result = await agent.run("Calculate 5 + 3")
        print(f"  Result: {result}")
        print(f"  Thoughts: {len(agent.thought_history)}")

        # Test Planning Agent
        print("\n[2] Planning Agent")
        print("-" * 40)

        planner = PlanningAgent("Planner")

        goal = planner.create_goal("Build a web application", priority=8)
        print(f"  Created goal: {goal['description']}")

        plan = planner.create_plan("Build a web application")
        print(f"  Created plan with {len(plan)} steps")

        status = planner.get_plan_status(list(planner.plans.keys())[0])
        print(f"  Plan status: {status['status']}")

        # Adjust plan
        adjusted = planner.adjust_plan(list(planner.plans.keys())[0], "Step 3 failed")
        print(f"  Adjusted plan: {len(adjusted)} steps")

        # Test Reflection Agent
        print("\n[3] Reflection Agent")
        print("-" * 40)

        reflector = ReflectionAgent("Reflector")

        reflector.record_experience("search", {"results": 10})
        reflector.record_experience("analyze", {"insights": 5})
        reflector.record_experience("search", None)  # Failed

        lessons = reflector.reflect_on_experiences(3)
        print(f"  Reflections: {len(lessons)}")

        performance = reflector.analyze_performance()
        print(f"  Success rate: {performance['success_rate']:.0%}")

        extracted = reflector.extract_lessons()
        print(f"  Lessons: {extracted[0] if extracted else 'None'}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()