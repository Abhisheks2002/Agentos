"""
Day 39: Planning Strategies
===========================
Skill: Planning
Mini Project: Plan Executor

Advanced planning and execution strategies for agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import deque


class PlanStatus(str, Enum):
    """Plan execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStrategy(str, Enum):
    """Planning strategies"""
    LINEAR = "linear"              # Sequential steps
    PARALLEL = "parallel"           # Concurrent execution
    CONDITIONAL = "conditional"     # Based on conditions
    HIERARCHICAL = "hierarchical"  # Nested sub-plans
    REACTIVE = "reactive"          # Adjust based on results
    MONTE_CARLO = "monte_carlo"    # Random sampling


@dataclass
class Step:
    """A step in a plan"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    action: Callable = None
    depends_on: List[str] = field(default_factory=list)
    condition: Callable = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 60.0

    # Execution state
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class Plan:
    """A plan with multiple steps"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[Step] = field(default_factory=list)
    strategy: PlanStrategy = PlanStrategy.LINEAR
    status: PlanStatus = PlanStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step(self, step_id: str) -> Optional[Step]:
        """Get a step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[Step]:
        """Get steps ready to execute"""
        ready = []
        for step in self.steps:
            if step.status != PlanStatus.PENDING:
                continue

            # Check dependencies
            deps_met = True
            for dep_id in step.depends_on:
                dep_step = self.get_step(dep_id)
                if not dep_step or dep_step.status != PlanStatus.COMPLETED:
                    deps_met = False
                    break

            if deps_met:
                # Check condition
                if step.condition:
                    try:
                        if not step.condition():
                            deps_met = False
                    except:
                        deps_met = False

            if deps_met:
                ready.append(step)

        return ready


class LinearPlanner:
    """Creates and executes linear plans"""

    def create_plan(self, steps: List[Dict]) -> Plan:
        """Create a linear plan"""
        plan = Plan(
            name="Linear Plan",
            strategy=PlanStrategy.LINEAR
        )

        for i, step_data in enumerate(steps):
            step = Step(
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", ""),
                action=step_data.get("action"),
                depends_on=[plan.steps[-1].id] if plan.steps else []
            )
            plan.steps.append(step)

        return plan


class ParallelPlanner:
    """Creates and executes parallel plans"""

    def create_plan(self, steps: List[Dict]) -> Plan:
        """Create a parallel plan"""
        plan = Plan(
            name="Parallel Plan",
            strategy=PlanStrategy.PARALLEL
        )

        for i, step_data in enumerate(steps):
            step = Step(
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", ""),
                action=step_data.get("action"),
                depends_on=step_data.get("depends_on", [])
            )
            plan.steps.append(step)

        return plan


class HierarchicalPlanner:
    """Creates hierarchical plans with sub-plans"""

    def __init__(self):
        self.sub_plans: Dict[str, Plan] = {}

    def create_plan(self, plan_data: Dict) -> Plan:
        """Create a hierarchical plan"""
        plan = Plan(
            name=plan_data.get("name", "Hierarchical Plan"),
            description=plan_data.get("description", ""),
            strategy=PlanStrategy.HIERARCHICAL
        )

        for step_data in plan_data.get("steps", []):
            if "sub_plan" in step_data:
                # Create sub-plan
                sub_plan = self.create_plan(step_data["sub_plan"])
                self.sub_plans[sub_plan.id] = sub_plan

                step = Step(
                    name=step_data["name"],
                    description=step_data.get("description", ""),
                )
                step.metadata["sub_plan_id"] = sub_plan.id
            else:
                step = Step(
                    name=step_data.get("name", ""),
                    description=step_data.get("description", ""),
                    action=step_data.get("action")
                )

            plan.steps.append(step)

        return plan


class ConditionalPlanner:
    """Creates plans with conditional execution"""

    def create_plan(self, steps: List[Dict]) -> Plan:
        """Create a conditional plan"""
        plan = Plan(
            name="Conditional Plan",
            strategy=PlanStrategy.CONDITIONAL
        )

        for step_data in steps:
            step = Step(
                name=step_data.get("name", ""),
                description=step_data.get("description", ""),
                action=step_data.get("action"),
                condition=step_data.get("condition"),
                depends_on=step_data.get("depends_on", [])
            )
            plan.steps.append(step)

        return plan


class PlanExecutor:
    """Executes plans with various strategies"""

    def __init__(self):
        self.current_plan: Optional[Plan] = None
        self.execution_history: List[Plan] = []

    async def execute(self, plan: Plan, context: Dict = None) -> Dict[str, Any]:
        """Execute a plan"""
        self.current_plan = plan
        plan.status = PlanStatus.RUNNING
        plan.started_at = datetime.now().isoformat()
        context = context or {}

        results = {}

        try:
            if plan.strategy == PlanStrategy.LINEAR:
                results = await self._execute_linear(plan, context)
            elif plan.strategy == PlanStrategy.PARALLEL:
                results = await self._execute_parallel(plan, context)
            elif plan.strategy == PlanStrategy.CONDITIONAL:
                results = await self._execute_conditional(plan, context)
            elif plan.strategy == PlanStrategy.HIERARCHICAL:
                results = await self._execute_hierarchical(plan, context)
            else:
                results = await self._execute_linear(plan, context)

            plan.status = PlanStatus.COMPLETED

        except Exception as e:
            plan.status = PlanStatus.FAILED
            results["error"] = str(e)

        plan.completed_at = datetime.now().isoformat()
        self.execution_history.append(plan)

        return results

    async def _execute_linear(self, plan: Plan, context: Dict) -> Dict[str, Any]:
        """Execute plan linearly"""
        results = {}

        while True:
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break

            step = ready_steps[0]
            await self._execute_step(step, context)
            results[step.id] = step.result

            if step.status == PlanStatus.FAILED:
                break

        return results

    async def _execute_parallel(self, plan: Plan, context: Dict) -> Dict[str, Any]:
        """Execute plan in parallel"""
        results = {}

        while True:
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break

            # Execute all ready steps in parallel
            tasks = [self._execute_step(step, context) for step in ready_steps]
            await asyncio.gather(*tasks, return_exceptions=True)

            for step in ready_steps:
                results[step.id] = step.result

            # Check if all done
            if all(s.status in [PlanStatus.COMPLETED, PlanStatus.FAILED] for s in plan.steps):
                break

        return results

    async def _execute_conditional(self, plan: Plan, context: Dict) -> Dict[str, Any]:
        """Execute plan with conditions"""
        results = {}

        while True:
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break

            step = ready_steps[0]
            await self._execute_step(step, context)
            results[step.id] = step.result

            if step.status == PlanStatus.FAILED:
                break

            # Check remaining steps' conditions with new result
            for remaining in plan.steps:
                if remaining.status == PlanStatus.PENDING and remaining.condition:
                    try:
                        remaining.condition = lambda: remaining.condition(results)
                    except:
                        pass

        return results

    async def _execute_hierarchical(self, plan: Plan, context: Dict) -> Dict[str, Any]:
        """Execute hierarchical plan"""
        results = {}

        while True:
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break

            step = ready_steps[0]

            # Check for sub-plan
            if "sub_plan_id" in step.metadata:
                sub_plan = None
                for p in self.execution_history:
                    if p.id == step.metadata["sub_plan_id"]:
                        sub_plan = p

                if sub_plan:
                    step.result = {s.id: s.result for s in sub_plan.steps}
            else:
                await self._execute_step(step, context)

            results[step.id] = step.result

            if step.status == PlanStatus.FAILED:
                break

        return results

    async def _execute_step(self, step: Step, context: Dict):
        """Execute a single step"""
        step.status = PlanStatus.RUNNING
        step.started_at = datetime.now().isoformat()

        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(step.action):
                step.result = await asyncio.wait_for(
                    step.action(context, step.result),
                    timeout=step.timeout
                )
            else:
                step.result = step.action(context, step.result)

            step.status = PlanStatus.COMPLETED

        except asyncio.TimeoutError:
            step.error = "Timeout"
            step.status = PlanStatus.FAILED

            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = PlanStatus.PENDING

        except Exception as e:
            step.error = str(e)
            step.status = PlanStatus.FAILED

            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = PlanStatus.PENDING

        step.completed_at = datetime.now().isoformat()

    def get_plan_status(self, plan: Plan) -> Dict[str, Any]:
        """Get plan execution status"""
        return {
            "plan_id": plan.id,
            "name": plan.name,
            "status": plan.status.value,
            "total_steps": len(plan.steps),
            "completed": sum(1 for s in plan.steps if s.status == PlanStatus.COMPLETED),
            "failed": sum(1 for s in plan.steps if s.status == PlanStatus.FAILED),
            "pending": sum(1 for s in plan.steps if s.status == PlanStatus.PENDING)
        }


class ReactivePlanner:
    """Creates and executes reactive plans"""

    def __init__(self):
        self.plans: List[Plan] = []
        self.current_plan: Optional[Plan] = None

    async def plan(self, goal: str, observations: List[Dict]) -> Plan:
        """Create a reactive plan based on observations"""
        plan = Plan(
            name=f"Reactive Plan: {goal}",
            strategy=PlanStrategy.REACTIVE
        )

        # Simple planning based on observations
        steps_data = [
            {"name": "analyze", "description": "Analyze current state"},
            {"name": "plan", "description": "Plan next action"},
            {"name": "execute", "description": "Execute action"},
            {"name": "evaluate", "description": "Evaluate result"}
        ]

        for step_data in steps_data:
            step = Step(
                name=step_data["name"],
                description=step_data["description"]
            )
            plan.steps.append(step)

        self.plans.append(plan)
        return plan


# Demo
def run_demo():
    print("=" * 70)
    print("Planning Strategies Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Test Linear Plan
        print("\n[1] Linear Plan")
        print("-" * 40)

        planner = LinearPlanner()
        executor = PlanExecutor()

        steps = [
            {"name": "fetch data", "action": lambda ctx, _: "data fetched"},
            {"name": "process", "action": lambda ctx, r: f"processed {r}"},
            {"name": "save", "action": lambda ctx, r: f"saved {r}"}
        ]

        plan = planner.create_plan(steps)
        results = await executor.execute(plan)

        print(f"  Steps: {len(plan.steps)}")
        print(f"  Results: {results}")

        # Test Parallel Plan
        print("\n[2] Parallel Plan")
        print("-" * 40)

        parallel_planner = ParallelPlanner()

        steps = [
            {"name": "task A", "action": lambda ctx, _: "A done"},
            {"name": "task B", "action": lambda ctx, _: "B done"},
            {"name": "task C", "action": lambda ctx, _: "C done"}
        ]

        plan = parallel_planner.create_plan(steps)
        results = await executor.execute(plan)

        print(f"  Steps: {len(plan.steps)}")
        print(f"  Results: {results}")

        # Test Conditional Plan
        print("\n[3] Conditional Plan")
        print("-" * 40)

        conditional_planner = ConditionalPlanner()
        context = {"has_data": True}

        def has_data(ctx):
            return ctx.get("has_data", False)

        steps = [
            {
                "name": "check data",
                "condition": lambda: has_data(context),
                "action": lambda ctx, _: "data exists"
            },
            {
                "name": "process data",
                "action": lambda ctx, r: f"processed: {r}"
            }
        ]

        plan = conditional_planner.create_plan(steps)
        results = await executor.execute(plan)

        print(f"  Conditional execution: {results}")

        # Plan status
        print("\n[4] Plan Status")
        print("-" * 40)

        status = executor.get_plan_status(plan)
        print(f"  Status: {status}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()