"""
Day 38: Reflection and Planning
===============================
Skill: Agent Self-Improvement
Mini Project: Self-Planning Agent

Building agents that can reflect on their work and plan ahead.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re


class ReflectionLevel(str, Enum):
    """Levels of reflection"""
    NONE = "none"
    SURFACE = "surface"      # What happened
    DEEP = "deep"            # Why it happened
    META = "meta"            # How to improve


class PlanStatus(str, Enum):
    """Plan execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVISED = "revised"


@dataclass
class Action:
    """An action taken by the agent"""
    name: str
    input_data: Any
    output_data: Any = None
    success: bool = False
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0


@dataclass
class Reflection:
    """A reflection on actions taken"""
    level: ReflectionLevel
    what_happened: str = ""
    why_it_happened: str = ""
    how_to_improve: str = ""
    insights: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PlanStep:
    """A step in a plan"""
    id: str
    description: str
    status: PlanStatus = PlanStatus.PENDING
    completed: bool = False
    result: Any = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: int = 1  # 1-5 scale


@dataclass
class Plan:
    """A plan of action"""
    id: str
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    revised_count: int = 0


class ReflectionEngine:
    """Engine for agent reflection"""

    def __init__(self, level: ReflectionLevel = ReflectionLevel.DEEP):
        self.level = level
        self.action_history: List[Action] = []
        self.reflections: List[Reflection] = []

    def record_action(self, action: Action):
        """Record an action"""
        self.action_history.append(action)

    def reflect(self, prompt: str = None) -> Reflection:
        """Generate a reflection"""
        if self.level == ReflectionLevel.NONE:
            return None

        reflection = Reflection(level=self.level)

        # Analyze recent actions
        recent_actions = self.action_history[-10:]

        # What happened
        if recent_actions:
            successful = [a for a in recent_actions if a.success]
            failed = [a for a in recent_actions if not a.success]

            reflection.what_happened = f"Completed {len(successful)} actions successfully"
            if failed:
                reflection.what_happened += f", {len(failed)} failed"

        # Why it happened (deep reflection)
        if self.level in [ReflectionLevel.DEEP, ReflectionLevel.META]:
            if failed := [a for a in recent_actions if not a.success]:
                reasons = []
                for action in failed:
                    if "timeout" in str(action.error).lower():
                        reasons.append("Operation timed out")
                    elif "permission" in str(action.error).lower():
                        reasons.append("Permission denied")
                    else:
                        reasons.append("Unknown error")

                reflection.why_it_happened = "; ".join(reasons)

        # How to improve (meta reflection)
        if self.level == ReflectionLevel.META:
            improvements = []

            # Analyze patterns
            if len(failed) > len(successful) / 2:
                improvements.append("Consider breaking tasks into smaller steps")

            if any(a.duration_ms > 5000 for a in recent_actions):
                improvements.append("Some operations taking too long - consider optimization")

            reflection.how_to_improve = "; ".join(improvements) if improvements else "No major improvements needed"

        self.reflections.append(reflection)
        return reflection

    def get_insights(self) -> List[str]:
        """Get accumulated insights"""
        insights = []
        for ref in self.reflections:
            insights.extend(ref.insights)
            if ref.how_to_improve:
                insights.append(ref.how_to_improve)
        return insights


class PlanningEngine:
    """Engine for planning and plan execution"""

    def __init__(self):
        self.plans: Dict[str, Plan] = {}
        self.current_plan_id: Optional[str] = None

    def create_plan(self, goal: str) -> Plan:
        """Create a new plan"""
        plan = Plan(id=str(datetime.now().timestamp()), goal=goal)
        self.plans[plan.id] = plan
        return plan

    def add_step(
        self,
        plan_id: str,
        description: str,
        dependencies: List[str] = None,
        estimated_effort: int = 1
    ) -> PlanStep:
        """Add a step to a plan"""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        step = PlanStep(
            id=f"step-{len(plan.steps)}",
            description=description,
            dependencies=dependencies or [],
            estimated_effort=estimated_effort
        )
        plan.steps.append(step)
        return step

    def generate_plan(self, goal: str, context: str = "") -> Plan:
        """Generate a plan from a goal (simple rule-based)"""
        plan = self.create_plan(goal)

        # Simple plan generation based on keywords
        goal_lower = goal.lower()

        if "analyze" in goal_lower:
            self.add_step(plan.id, "Gather data", estimated_effort=2)
            self.add_step(plan.id, "Process data", dependencies=["step-0"], estimated_effort=3)
            self.add_step(plan.id, "Generate insights", dependencies=["step-1"], estimated_effort=2)

        elif "build" in goal_lower or "create" in goal_lower:
            self.add_step(plan.id, "Design structure", estimated_effort=3)
            self.add_step(plan.id, "Implement core functionality", dependencies=["step-0"], estimated_effort=5)
            self.add_step(plan.id, "Add tests", dependencies=["step-1"], estimated_effort=2)
            self.add_step(plan.id, "Document", dependencies=["step-2"], estimated_effort=1)

        elif "research" in goal_lower:
            self.add_step(plan.id, "Search for information", estimated_effort=3)
            self.add_step(plan.id, "Compile findings", dependencies=["step-0"], estimated_effort=2)
            self.add_step(plan.id, "Summarize results", dependencies=["step-1"], estimated_effort=2)

        else:
            # Default plan
            self.add_step(plan.id, "Understand the task", estimated_effort=2)
            self.add_step(plan.id, "Execute main action", estimated_effort=3)
            self.add_step(plan.id, "Verify results", estimated_effort=2)

        plan.status = PlanStatus.PENDING
        return plan

    def get_next_step(self, plan_id: str) -> Optional[PlanStep]:
        """Get the next step to execute"""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        for step in plan.steps:
            if step.status == PlanStatus.PENDING:
                # Check dependencies
                deps_met = True
                for dep_id in step.dependencies:
                    dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                    if not dep_step or not dep_step.completed:
                        deps_met = False
                        break

                if deps_met:
                    return step

        return None

    def complete_step(self, plan_id: str, step_id: str, result: Any = None):
        """Mark a step as completed"""
        plan = self.plans.get(plan_id)
        if not plan:
            return

        for step in plan.steps:
            if step.id == step_id:
                step.completed = True
                step.status = PlanStatus.COMPLETED
                step.result = result
                break

        # Check if plan is complete
        if all(s.completed for s in plan.steps):
            plan.status = PlanStatus.COMPLETED

    def revise_plan(self, plan_id: str, reason: str) -> Plan:
        """Revise a plan"""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        # Mark current status
        plan.status = PlanStatus.REVISED
        plan.revised_count += 1

        # Create new plan based on previous
        new_plan = self.create_plan(plan.goal)
        new_plan.steps = plan.steps.copy()
        new_plan.status = PlanStatus.PENDING

        return new_plan


class SelfPlanningAgent:
    """An agent that can plan and reflect"""

    def __init__(self, agent_id: str, reflection_level: ReflectionLevel = ReflectionLevel.DEEP):
        self.agent_id = agent_id
        self.reflection_engine = ReflectionEngine(reflection_level)
        self.planning_engine = PlanningEngine()
        self.current_plan: Optional[Plan] = None

    async def think(self, goal: str, context: str = "") -> Plan:
        """Think and create a plan"""
        # Generate plan
        plan = self.planning_engine.generate_plan(goal, context)
        self.current_plan = plan
        return plan

    async def execute_plan(self, executor: Callable[[PlanStep], Any]) -> Dict[str, Any]:
        """Execute the current plan"""
        if not self.current_plan:
            return {"error": "No plan to execute"}

        results = []
        plan_id = self.current_plan.id

        while True:
            step = self.planning_engine.get_next_step(plan_id)
            if not step:
                break

            step.status = PlanStatus.IN_PROGRESS

            try:
                result = await executor(step) if asyncio.iscoroutinefunction(executor) else executor(step)
                self.planning_engine.complete_step(plan_id, step.id, result)

                # Record action
                action = Action(
                    name=step.description,
                    input_data=step.id,
                    output_data=result,
                    success=True
                )
                self.reflection_engine.record_action(action)

                results.append({"step": step.id, "result": result})

            except Exception as e:
                step.status = PlanStatus.FAILED
                step.error = str(e)

                action = Action(
                    name=step.description,
                    input_data=step.id,
                    error=str(e),
                    success=False
                )
                self.reflection_engine.record_action(action)

                results.append({"step": step.id, "error": str(e)})
                break

        return {
            "plan_id": plan_id,
            "status": self.current_plan.status,
            "results": results
        }

    async def reflect_on_results(self) -> Reflection:
        """Reflect on execution results"""
        return self.reflection_engine.reflect()


import asyncio


# Demo
def run_demo():
    print("=" * 70)
    print("Reflection and Planning Demo")
    print("=" * 70)

    async def demo():
        # Create self-planning agent
        print("\n[1] Self-Planning Agent")
        print("-" * 40)

        agent = SelfPlanningAgent("agent-1", ReflectionLevel.META)

        # Think about a goal
        plan = await agent.think("Build a data analysis pipeline")
        print(f"  Created plan with {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"    - {step.description} (effort: {step.estimated_effort})")

        # Execute plan
        print("\n[2] Execute Plan")
        print("-" * 40)

        async def executor(step: PlanStep):
            print(f"    Executing: {step.description}")
            await asyncio.sleep(0.1)
            return f"Result of {step.description}"

        results = await agent.execute_plan(executor)
        print(f"  Completed: {len(results['results'])} steps")

        # Reflect
        print("\n[3] Reflection")
        print("-" * 40)

        reflection = await agent.reflect_on_results()
        print(f"  Level: {reflection.level.value}")
        print(f"  What: {reflection.what_happened}")
        print(f"  Why: {reflection.why_it_happened}")
        print(f"  Improvement: {reflection.how_to_improve}")

        # Plan revision
        print("\n[4] Plan Revision")
        print("-" * 40)

        new_plan = agent.planning_engine.revise_plan(plan.id, "Initial plan failed")
        print(f"  Revised plan: {new_plan.id}")
        print(f"  Revision count: {new_plan.revised_count}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()