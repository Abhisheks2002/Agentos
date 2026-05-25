"""
Day 29: Agent Task Delegation
==============================
Skill: Task Assignment
Mini Project: Delegation System

Efficiently delegating tasks to appropriate agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(str, Enum):
    """Agent capabilities"""
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    WRITING = "writing"
    DESIGN = "design"
    COORDINATION = "coordination"
    REVIEW = "review"


@dataclass
class Task:
    """A delegatable task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    required_capabilities: List[AgentCapability] = field(default_factory=list)
    assigned_to: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


@dataclass
class AgentProfile:
    """Profile of an agent's capabilities"""
    id: str = ""
    name: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    current_load: int = 0
    max_load: int = 5
    performance_score: float = 1.0
    available: bool = True


class TaskDelegator:
    """Delegates tasks to appropriate agents"""

    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self.tasks: Dict[str, Task] = {}
        self.delegation_history: List[Dict] = []

    def register_agent(self, profile: AgentProfile):
        """Register an agent"""
        self.agents[profile.id] = profile

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].available = False

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        capabilities: List[AgentCapability] = None
    ) -> Task:
        """Create a new task"""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            required_capabilities=capabilities or []
        )
        self.tasks[task.id] = task
        return task

    def find_best_agent(self, task: Task) -> Optional[AgentProfile]:
        """Find the best agent for a task"""
        suitable = []

        for agent in self.agents.values():
            if not agent.available:
                continue

            if agent.current_load >= agent.max_load:
                continue

            # Check capabilities
            has_capabilities = all(
                cap in agent.capabilities
                for cap in task.required_capabilities
            )

            if has_capabilities:
                # Score based on load and performance
                score = agent.performance_score / (agent.current_load + 1)
                suitable.append((agent, score))

        if not suitable:
            return None

        # Return highest scored agent
        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable[0][0]

    async def delegate_task(self, task_id: str) -> bool:
        """Delegate a task to an appropriate agent"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False

        # Find best agent
        agent = self.find_best_agent(task)
        if not agent:
            return False

        # Assign task
        task.assigned_to = agent.id
        task.status = TaskStatus.ASSIGNED
        agent.current_load += 1

        # Record delegation
        self.delegation_history.append({
            "task_id": task.id,
            "agent_id": agent.id,
            "timestamp": datetime.now().isoformat()
        })

        return True

    async def complete_task(self, task_id: str, result: Any) -> bool:
        """Mark task as completed"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now().isoformat()

        # Update agent load
        if task.assigned_to and task.assigned_to in self.agents:
            self.agents[task.assigned_to].current_load -= 1

        return True

    def get_delegation_stats(self) -> Dict[str, Any]:
        """Get delegation statistics"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)

        return {
            "total_tasks": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "completion_rate": completed / total if total > 0 else 0
        }

    def get_agent_workload(self) -> Dict[str, int]:
        """Get current workload per agent"""
        return {aid: agent.current_load for aid, agent in self.agents.items()}


class SkillBasedDelegator(TaskDelegator):
    """Delegator with skill matching"""

    def find_best_agent(self, task: Task) -> Optional[AgentProfile]:
        """Find best agent with skill matching"""
        # Weight primary capability more heavily
        if not task.required_capabilities:
            return super().find_best_agent(task)

        primary_cap = task.required_capabilities[0]
        suitable = []

        for agent in self.agents.values():
            if not agent.available or agent.current_load >= agent.max_load:
                continue

            # Check primary capability
            if primary_cap not in agent.capabilities:
                continue

            # Calculate score
            cap_count = len([c for c in task.required_capabilities if c in agent.capabilities])
            score = (agent.performance_score * cap_count) / (agent.current_load + 1)
            suitable.append((agent, score))

        if not suitable:
            return None

        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable[0][0]


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Task Delegation Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create delegator
        delegator = TaskDelegator()

        # Register agents
        print("\n[1] Register Agents")
        print("-" * 40)

        agents = [
            AgentProfile(id="agent1", name="CodeBot", capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.REVIEW
            ], max_load=3),
            AgentProfile(id="agent2", name="DataBot", capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.CODE_GENERATION
            ], max_load=4),
            AgentProfile(id="agent3", name="ResearchBot", capabilities=[
                AgentCapability.RESEARCH,
                AgentCapability.WRITING
            ], max_load=5)
        ]

        for agent in agents:
            delegator.register_agent(agent)

        print(f"  Registered {len(agents)} agents")

        # Create tasks
        print("\n[2] Create Tasks")
        print("-" * 40)

        tasks = [
            delegator.create_task(
                "Build API",
                "Create a REST API",
                TaskPriority.HIGH,
                [AgentCapability.CODE_GENERATION]
            ),
            delegator.create_task(
                "Analyze Data",
                "Analyze sales data",
                TaskPriority.NORMAL,
                [AgentCapability.DATA_ANALYSIS]
            ),
            delegator.create_task(
                "Write Docs",
                "Write documentation",
                TaskPriority.LOW,
                [AgentCapability.WRITING]
            )
        ]

        print(f"  Created {len(tasks)} tasks")

        # Delegate tasks
        print("\n[3] Delegate Tasks")
        print("-" * 40)

        for task in tasks:
            success = await delegator.delegate_task(task.id)
            print(f"  {task.title}: {'Delegated' if success else 'Failed'} -> {task.assigned_to}")

        # Complete a task
        print("\n[4] Complete Task")
        print("-" * 40)

        await delegator.complete_task(tasks[0].id, {"api": "created"})
        print(f"  Completed: {tasks[0].title}")

        # Stats
        print("\n[5] Delegation Stats")
        print("-" * 40)

        stats = delegator.get_delegation_stats()
        print(f"  Total: {stats['total_tasks']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Completion rate: {stats['completion_rate']:.0%}")

        # Workload
        print("\n[6] Agent Workload")
        print("-" * 40)

        workload = delegator.get_agent_workload()
        for agent_id, load in workload.items():
            print(f"  {agent_id}: {load} tasks")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()