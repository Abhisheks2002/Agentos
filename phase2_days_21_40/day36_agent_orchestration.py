"""
Day 36: Agent Orchestration Patterns
====================================
Skill: Orchestration
Mini Project: Task Queue Manager

Mastering agent orchestration and task distribution.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import deque
from heapq import heappush, heappop


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task in the orchestration system"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    input_data: Any = None
    output_data: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


class Agent:
    """An agent that can execute tasks"""

    def __init__(self, agent_id: str, name: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities or []
        self.current_task: Optional[Task] = None
        self.task_history: List[Task] = []
        self.available = True

    async def execute_task(self, task: Task) -> Any:
        """Execute a task"""
        task.status = TaskStatus.RUNNING
        task.assigned_agent = self.agent_id
        task.started_at = datetime.now().isoformat()
        self.current_task = task
        self.available = False

        try:
            # Simulate task execution
            await asyncio.sleep(0.5)

            # Process task based on name
            if "analyze" in task.name.lower():
                result = f"Analysis complete: {task.input_data}"
            elif "process" in task.name.lower():
                result = f"Processing complete: {task.input_data}"
            elif "fetch" in task.name.lower():
                result = f"Fetched: {task.input_data}"
            else:
                result = f"Task {task.id} completed"

            task.output_data = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()

            self.task_history.append(task)
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
            raise

        finally:
            self.current_task = None
            self.available = True


class TaskQueue:
    """Priority-based task queue"""

    def __init__(self):
        self.heap: List[tuple] = []  # (priority_order, task)
        self.tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self._priority_map = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3
        }

    def enqueue(self, task: Task) -> str:
        """Add a task to the queue"""
        self.tasks[task.id] = task
        priority = self._priority_map[task.priority]
        heappush(self.heap, (priority, task.id, task))
        return task.id

    def dequeue(self) -> Optional[Task]:
        """Get the highest priority task"""
        if not self.heap:
            return None

        _, task_id, task = heappop(self.heap)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def mark_completed(self, task: Task):
        """Mark a task as completed"""
        if task.id in self.tasks:
            del self.tasks[task.id]
        self.completed_tasks.append(task)

    def get_pending(self) -> List[Task]:
        """Get all pending tasks"""
        return list(self.tasks.values())

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            "pending": len(self.tasks),
            "completed": len(self.completed_tasks),
            "by_priority": {
                p.value: len([t for t in self.tasks.values() if t.priority == p])
                for p in TaskPriority
            }
        }


class Orchestrator:
    """Orchestrates tasks across agents"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = TaskQueue()
        self.running = False

    def register_agent(self, agent: Agent):
        """Register an agent"""
        self.agents[agent.agent_id] = agent

    def find_available_agent(self, required_capability: str = None) -> Optional[Agent]:
        """Find an available agent"""
        for agent in self.agents.values():
            if agent.available:
                if required_capability is None or required_capability in agent.capabilities:
                    return agent
        return None

    def find_best_agent(self, task: Task) -> Optional[Agent]:
        """Find the best agent for a task"""
        # Find available agent with matching capability
        for agent in self.agents.values():
            if agent.available and any(cap in task.name.lower() for cap in agent.capabilities):
                return agent

        # Fall back to any available agent
        return self.find_available_agent()

    async def submit_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Any = None,
        dependencies: List[str] = None
    ) -> str:
        """Submit a new task"""
        task = Task(
            name=name,
            description=description,
            priority=priority,
            input_data=input_data,
            dependencies=dependencies or []
        )

        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self.task_queue.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.PENDING

        return self.task_queue.enqueue(task)

    async def process_tasks(self):
        """Process tasks from the queue"""
        self.running = True

        while self.running:
            # Check for pending tasks
            task = self.task_queue.dequeue()

            if not task:
                await asyncio.sleep(0.1)
                continue

            # Check if dependencies are met
            deps_met = True
            for dep_id in task.dependencies:
                dep_task = self.task_queue.get_task(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    deps_met = False
                    break

            if not deps_met:
                # Re-queue and check later
                self.task_queue.enqueue(task)
                await asyncio.sleep(0.1)
                continue

            # Find an agent
            agent = self.find_best_agent(task)

            if not agent:
                # Re-queue and wait
                self.task_queue.enqueue(task)
                await asyncio.sleep(0.1)
                continue

            # Execute the task
            try:
                result = await agent.execute_task(task)
                self.task_queue.mark_completed(task)
            except Exception as e:
                # Handle failure
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    self.task_queue.enqueue(task)

    def stop(self):
        """Stop the orchestrator"""
        self.running = False


class WorkflowOrchestrator:
    """Orchestrates multi-step workflows"""

    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.workflows: Dict[str, List[Task]] = {}

    async def create_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """Create a workflow with multiple steps"""
        workflow_id = str(uuid.uuid4())
        tasks = []

        prev_task_id = None

        for step in steps:
            task_id = await self.orchestrator.submit_task(
                name=step["name"],
                description=step.get("description", ""),
                priority=TaskPriority(step.get("priority", "normal")),
                input_data=step.get("input"),
                dependencies=[prev_task_id] if prev_task_id else []
            )

            tasks.append(self.orchestrator.task_queue.get_task(task_id))
            prev_task_id = task_id

        self.workflows[workflow_id] = tasks
        return workflow_id

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        tasks = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "total_steps": len(tasks),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "status": "completed" if all(t.status == TaskStatus.COMPLETED for t in tasks)
                       else "failed" if any(t.status == TaskStatus.FAILED for t in tasks)
                       else "running"
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Orchestration Patterns Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create orchestrator
        orchestrator = Orchestrator()

        # Register agents
        print("\n[1] Register Agents")
        print("-" * 40)

        agent1 = Agent("agent-1", "Data Agent", ["analyze", "process"])
        agent2 = Agent("agent-2", "Fetch Agent", ["fetch", "analyze"])
        agent3 = Agent("agent-3", "Process Agent", ["process"])

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        print(f"  Registered: {agent1.name}, {agent2.name}, {agent3.name}")

        # Submit tasks
        print("\n[2] Submit Tasks")
        print("-" * 40)

        await orchestrator.submit_task(
            "analyze data",
            "Analyze the dataset",
            TaskPriority.HIGH,
            {"dataset": "sales_2024"}
        )

        await orchestrator.submit_task(
            "fetch records",
            "Fetch database records",
            TaskPriority.NORMAL,
            {"table": "users"}
        )

        await orchestrator.submit_task(
            "process images",
            "Process image files",
            TaskPriority.LOW,
            {"files": ["img1.jpg", "img2.jpg"]}
        )

        await orchestrator.submit_task(
            "critical task",
            "Critical system task",
            TaskPriority.CRITICAL,
            {"action": "backup"}
        )

        stats = orchestrator.task_queue.get_stats()
        print(f"  Queued: {stats['pending']} tasks")
        print(f"  By priority: {stats['by_priority']}")

        # Process tasks
        print("\n[3] Process Tasks")
        print("-" * 40)

        # Start processor in background
        process_task = asyncio.create_task(orchestrator.process_tasks())

        # Give it time to process
        await asyncio.sleep(2)

        orchestrator.stop()
        process_task.cancel()

        print(f"  Completed: {len(orchestrator.task_queue.completed_tasks)} tasks")

        # Workflow
        print("\n[4] Workflow Orchestration")
        print("-" * 40)

        workflow_orch = WorkflowOrchestrator(orchestrator)

        workflow_id = await workflow_orch.create_workflow(
            "data_pipeline",
            [
                {"name": "fetch data", "priority": "high"},
                {"name": "process data", "priority": "normal"},
                {"name": "analyze results", "priority": "normal"}
            ]
        )

        status = workflow_orch.get_workflow_status(workflow_id)
        print(f"  Created workflow: {workflow_id}")
        print(f"  Steps: {status['total_steps']}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()