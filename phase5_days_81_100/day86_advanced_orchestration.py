"""
Day 86: Advanced Agent Orchestration
=====================================

Implementing advanced orchestration patterns for coordinating multiple agents
including hierarchical structures, supervisor patterns, and complex workflow
coordination.

Key Concepts:
- Hierarchical Agent Teams
- Supervisor/Monitor Pattern
- Sequential and Parallel Execution
- Dependency Graphs
- Dynamic Task Distribution
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
from collections import defaultdict
import json


class AgentRole(Enum):
    """Agent roles in orchestration"""
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    ORCHESTRATOR = "orchestrator"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutionMode(Enum):
    """Task execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    FANOUT_FANIN = "fanout_fanin"


@dataclass
class AgentCapability:
    """Agent capability definition"""
    capability_id: str
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    cost_estimate: float = 1.0


@dataclass
class OrchestratedAgent:
    """Agent participating in orchestration"""
    agent_id: str
    name: str
    role: AgentRole
    capabilities: List[AgentCapability]
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    status: str = "idle"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Orchestrated task"""
    task_id: str
    name: str
    description: str
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    output: Any
    execution_time: float
    agent_id: str
    error: Optional[str] = None


class HierarchicalTeam:
    """
    Hierarchical Agent Team
    ======================

    Implements a tree structure where supervisors coordinate workers.
    """

    def __init__(self, team_id: str, name: str):
        self.team_id = team_id
        self.name = name
        self.agents: Dict[str, OrchestratedAgent] = {}
        self.supervisor_tree: Dict[str, List[str]] = defaultdict(list)
        self.task_queue: asyncio.Queue = asyncio.Queue()

    def register_agent(self, agent: OrchestratedAgent):
        """Register an agent in the team"""
        self.agents[agent.agent_id] = agent

    def set_supervisor(self, worker_id: str, supervisor_id: str):
        """Set supervisor relationship"""
        self.supervisor_tree[supervisor_id].append(worker_id)

    def get_supervisor(self, agent_id: str) -> Optional[str]:
        """Get supervisor for an agent"""
        for supervisor, workers in self.supervisor_tree.items():
            if agent_id in workers:
                return supervisor
        return None

    def get_workers(self, supervisor_id: str) -> List[OrchestratedAgent]:
        """Get workers under a supervisor"""
        worker_ids = self.supervisor_tree.get(supervisor_id, [])
        return [self.agents[wid] for wid in worker_ids if wid in self.agents]

    def find_capable_agent(self, capability: str) -> Optional[OrchestratedAgent]:
        """Find an agent with the required capability"""
        available = [
            a for a in self.agents.values()
            if a.current_tasks < a.max_concurrent_tasks
            and any(cap in c.name for c in a.capabilities)
        ]
        return min(available, key=lambda a: a.current_tasks) if available else None

    def get_team_status(self) -> Dict[str, Any]:
        """Get team status"""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "total_agents": len(self.agents),
            "agents": {
                aid: {
                    "name": a.name,
                    "role": a.role.value,
                    "status": a.status,
                    "current_tasks": a.current_tasks,
                    "max_concurrent": a.max_concurrent_tasks
                }
                for aid, a in self.agents.items()
            }
        }


class SupervisorPattern:
    """
    Supervisor Pattern
    ==================

    A supervisor monitors workers and can restart failed tasks,
    redistribute work, or escalate issues.
    """

    def __init__(self, supervisor_id: str, name: str):
        self.supervisor_id = supervisor_id
        self.name = name
        self.workers: Dict[str, OrchestratedAgent] = {}
        self.task_history: List[Task] = []
        self.failure_count: Dict[str, int] = defaultdict(int)
        self.max_retries = 3

    def add_worker(self, agent: OrchestratedAgent):
        """Add a worker to the supervisor"""
        self.workers[agent.agent_id] = agent

    async def supervise_task(self, task: Task) -> ExecutionResult:
        """Supervise task execution with error handling"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        while self.failure_count[task.task_id] < self.max_retries:
            # Find best worker
            worker = self._select_worker(task)
            if not worker:
                return ExecutionResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    output=None,
                    execution_time=0,
                    agent_id="",
                    error="No available workers"
                )

            # Execute task
            result = await self._execute_with_worker(task, worker)

            if result.status == TaskStatus.COMPLETED:
                self.failure_count[task.task_id] = 0
                return result
            else:
                self.failure_count[task.task_id] += 1
                task.error = result.error
                # Try next worker

        return ExecutionResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            output=None,
            execution_time=0,
            agent_id="",
            error=f"Max retries ({self.max_retries}) exceeded"
        )

    def _select_worker(self, task: Task) -> Optional[OrchestratedAgent]:
        """Select best worker for task"""
        capable = [
            w for w in self.workers.values()
            if w.current_tasks < w.max_concurrent_tasks
            and any(cap in str(task.input_data) for cap in [c.name for c in w.capabilities])
        ]
        return min(capable, key=lambda w: w.current_tasks) if capable else None

    async def _execute_with_worker(self, task: Task, worker: OrchestratedAgent) -> ExecutionResult:
        """Execute task with specific worker"""
        worker.current_tasks += 1
        worker.status = "executing"

        try:
            # Simulate task execution
            await asyncio.sleep(0.1)

            output = {"result": f"Task {task.name} completed by {worker.name}"}
            status = TaskStatus.COMPLETED

            return ExecutionResult(
                task_id=task.task_id,
                status=status,
                output=output,
                execution_time=0.1,
                agent_id=worker.agent_id
            )
        except Exception as e:
            return ExecutionResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                output=None,
                execution_time=0,
                agent_id=worker.agent_id,
                error=str(e)
            )
        finally:
            worker.current_tasks = max(0, worker.current_tasks - 1)
            worker.status = "idle"


class TaskDependencyGraph:
    """
    Task Dependency Graph
    =====================

    Manages complex task dependencies with parallel/sequential execution.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)

    def add_task(self, task: Task):
        """Add task to graph"""
        self.tasks[task.task_id] = task

    def add_dependency(self, task_id: str, depends_on: str):
        """Add dependency: task_id depends on depends_on"""
        self.adjacency[depends_on].append(task_id)
        self.reverse_adjacency[task_id].append(depends_on)
        self.tasks[task_id].dependencies.append(depends_on)

    def get_ready_tasks(self) -> List[str]:
        """Get tasks with all dependencies completed"""
        ready = []
        for task_id, task in self.tasks.items():
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_completed = all(
                self.tasks[d].status == TaskStatus.COMPLETED
                for d in task.dependencies
            )
            if deps_completed:
                ready.append(task_id)

        return ready

    def get_execution_order(self, mode: ExecutionMode) -> List[List[str]]:
        """Get execution order based on mode"""
        if mode == ExecutionMode.SEQUENTIAL:
            return [[tid] for tid in self.tasks.keys()]

        elif mode == ExecutionMode.PARALLEL:
            # All tasks can run in parallel
            return [list(self.tasks.keys())]

        elif mode == ExecutionMode.FANOUT_FANIN:
            # Group by dependency levels
            levels = []
            completed = set()
            remaining = set(self.tasks.keys())

            while remaining:
                # Find tasks with all dependencies satisfied
                current_level = [
                    tid for tid in remaining
                    if all(d in completed for d in self.tasks[tid].dependencies)
                ]

                if not current_level:
                    break

                levels.append(current_level)
                completed.update(current_level)
                remaining -= set(current_level)

            return levels

        return [[tid] for tid in self.tasks.keys()]


class DynamicOrchestrator:
    """
    Dynamic Task Orchestrator
    =========================

    Orchestrates tasks dynamically based on capabilities, load, and dependencies.
    """

    def __init__(self, orchestrator_id: str, name: str):
        self.orchestrator_id = orchestrator_id
        self.name = name
        self.teams: Dict[str, HierarchicalTeam] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.execution_mode = ExecutionMode.SEQUENTIAL

    def register_team(self, team: HierarchicalTeam):
        """Register a team of agents"""
        self.teams[team.team_id] = team

    async def execute_workflow(self, tasks: List[Task], mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> List[ExecutionResult]:
        """Execute a workflow of tasks"""
        self.execution_mode = mode

        # Build dependency graph
        graph = TaskDependencyGraph()
        for task in tasks:
            graph.add_task(task)
            for dep in task.dependencies:
                if dep in self.active_tasks:
                    graph.add_dependency(task.task_id, dep)

        results = []

        # Get execution plan
        execution_plan = graph.get_execution_order(mode)

        # Execute in order
        for level_tasks in execution_plan:
            # Execute all tasks in this level
            level_results = await asyncio.gather(
                *[self._execute_task(tid) for tid in level_tasks],
                return_exceptions=True
            )

            for i, result in enumerate(level_results):
                if isinstance(result, Exception):
                    results.append(ExecutionResult(
                        task_id=level_tasks[i],
                        status=TaskStatus.FAILED,
                        output=None,
                        execution_time=0,
                        agent_id="",
                        error=str(result)
                    ))
                else:
                    results.append(result)

        return results

    async def _execute_task(self, task_id: str) -> ExecutionResult:
        """Execute a single task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return ExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                output=None,
                execution_time=0,
                agent_id="",
                error="Task not found"
            )

        # Find capable agent across all teams
        for team in self.teams.values():
            agent = team.find_capable_agent(task.input_data.get("capability", ""))
            if agent:
                task.assigned_agent = agent.agent_id
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

                # Simulate execution
                await asyncio.sleep(0.1)

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.output_data = {"result": "completed"}

                return ExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    output=task.output_data,
                    execution_time=0.1,
                    agent_id=agent.agent_id
                )

        return ExecutionResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            output=None,
            execution_time=0,
            agent_id="",
            error="No capable agent found"
        )

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "orchestrator_id": self.orchestrator_id,
            "name": self.name,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "teams": {
                tid: team.get_team_status()
                for tid, team in self.teams.items()
            }
        }


class AgentMessage:
    """Message between orchestrated agents"""
    def __init__(self, message_id: str, sender: str, receiver: str, content: Any):
        self.message_id = message_id
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = datetime.now()


class MessageBus:
    """
    Inter-Agent Message Bus
    =======================

    Enables communication between agents in the orchestration.
    """

    def __init__(self):
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.messages: List[AgentMessage] = []

    def subscribe(self, agent_id: str, channel: str):
        """Subscribe agent to a channel"""
        self.subscriptions[channel].append(agent_id)

    def publish(self, sender: str, channel: str, content: Any):
        """Publish message to channel"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver="",
            content=content
        )
        self.messages.append(message)
        self.message_queue.put_nowait((channel, message))

        # Queue for subscribers
        for subscriber in self.subscriptions.get(channel, []):
            message.receiver = subscriber

    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        """Receive message for agent"""
        try:
            while True:
                channel, message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=timeout
                )
                if message.receiver == agent_id or message.receiver == "":
                    return message
        except asyncio.TimeoutError:
            return None


async def simulate_agent_execution(agent: OrchestratedAgent, task: Task) -> Dict[str, Any]:
    """Simulate agent executing a task"""
    agent.current_tasks += 1
    agent.status = "executing"

    await asyncio.sleep(0.1)

    agent.current_tasks = max(0, agent.current_tasks - 1)
    agent.status = "idle"

    return {
        "agent": agent.name,
        "task": task.name,
        "result": "completed"
    }


async def main():
    """Demonstrate Advanced Agent Orchestration"""
    print("=" * 60)
    print("Advanced Agent Orchestration - Day 86")
    print("=" * 60)

    # Create hierarchical team
    team = HierarchicalTeam("team-001", "Data Processing Team")

    # Register agents
    agents = [
        OrchestratedAgent(
            agent_id="supervisor-1",
            name="Data Supervisor",
            role=AgentRole.SUPERVISOR,
            capabilities=[
                AgentCapability("cap-1", "oversight", "Oversee data processing")
            ],
            max_concurrent_tasks=5
        ),
        OrchestratedAgent(
            agent_id="worker-1",
            name="ETL Worker",
            role=AgentRole.WORKER,
            capabilities=[
                AgentCapability("cap-2", "extract", "Extract data"),
                AgentCapability("cap-3", "transform", "Transform data"),
                AgentCapability("cap-4", "load", "Load data")
            ],
            max_concurrent_tasks=2
        ),
        OrchestratedAgent(
            agent_id="worker-2",
            name="Validation Worker",
            role=AgentRole.WORKER,
            capabilities=[
                AgentCapability("cap-5", "validate", "Validate data"),
                AgentCapability("cap-6", "quality_check", "Data quality checks")
            ],
            max_concurrent_tasks=3
        ),
        OrchestratedAgent(
            agent_id="specialist-1",
            name="Analytics Specialist",
            role=AgentRole.SPECIALIST,
            capabilities=[
                AgentCapability("cap-7", "analyze", "Analyze data"),
                AgentCapability("cap-8", "report", "Generate reports")
            ],
            max_concurrent_tasks=1
        )
    ]

    for agent in agents:
        team.register_agent(agent)

    # Set up supervisor relationships
    team.set_supervisor("worker-1", "supervisor-1")
    team.set_supervisor("worker-2", "supervisor-1")
    team.set_supervisor("specialist-1", "supervisor-1")

    print("\n[1] Hierarchical Team Structure")
    print("-" * 40)
    status = team.get_team_status()
    print(f"Team: {status['name']}")
    print(f"Total Agents: {status['total_agents']}")
    print("\nSupervisor: Data Supervisor")
    workers = team.get_workers("supervisor-1")
    for w in workers:
        print(f"  └── Worker: {w.name} ({w.role.value})")

    # Test supervisor pattern
    print("\n[2] Supervisor Pattern")
    print("-" * 40)
    supervisor = SupervisorPattern("sup-001", "Main Supervisor")
    supervisor.add_worker(agents[1])  # ETL Worker
    supervisor.add_worker(agents[2])  # Validation Worker

    task = Task(
        task_id="task-001",
        name="Process Data",
        description="Process and validate data",
        input_data={"capability": "transform", "data": [1, 2, 3]}
    )

    result = await supervisor.supervise_task(task)
    print(f"Task: {task.name}")
    print(f"Status: {result.status.value}")
    print(f"Agent: {result.agent_id}")
    print(f"Output: {result.output}")

    # Test dependency graph
    print("\n[3] Task Dependency Graph")
    print("-" * 40)
    graph = TaskDependencyGraph()

    task1 = Task(task_id="t1", name="Extract", description="", input_data={})
    task2 = Task(task_id="t2", name="Transform", description="", input_data={})
    task3 = Task(task_id="t3", name="Validate", description="", input_data={})
    task4 = Task(task_id="t4", name="Load", description="", input_data={})
    task5 = Task(task_id="t5", name="Report", description="", input_data={})

    graph.add_task(task1)
    graph.add_task(task2)
    graph.add_task(task3)
    graph.add_task(task4)
    graph.add_task(task5)

    # t2 depends on t1, t3 depends on t2, t4 depends on t3, t5 depends on t2
    graph.add_dependency("t2", "t1")
    graph.add_dependency("t3", "t2")
    graph.add_dependency("t4", "t3")
    graph.add_dependency("t5", "t2")

    execution_plan = graph.get_execution_order(ExecutionMode.FANOUT_FANIN)
    print("Dependency Graph:")
    print("  t1 (Extract)")
    print("    └── t2 (Transform)")
    print("          ├── t3 (Validate)")
    print("          │     └── t4 (Load)")
    print("          └── t5 (Report)")

    print("\nExecution Plan (Fanout-Fanin):")
    for i, level in enumerate(execution_plan):
        print(f"  Level {i+1}: {level}")

    # Test dynamic orchestrator
    print("\n[4] Dynamic Orchestrator")
    print("-" * 40)
    orchestrator = DynamicOrchestrator("orch-001", "Main Orchestrator")
    orchestrator.register_team(team)

    # Create workflow tasks
    workflow_tasks = [
        Task(
            task_id="wf1",
            name="Extract Data",
            description="Extract from source",
            input_data={"capability": "extract"}
        ),
        Task(
            task_id="wf2",
            name="Transform Data",
            description="Transform the data",
            input_data={"capability": "transform"},
            dependencies=["wf1"]
        ),
        Task(
            task_id="wf3",
            name="Validate Data",
            description="Validate the data",
            input_data={"capability": "validate"},
            dependencies=["wf2"]
        )
    ]

    for task in workflow_tasks:
        orchestrator.active_tasks[task.task_id] = task

    results = await orchestrator.execute_workflow(workflow_tasks, ExecutionMode.SEQUENTIAL)

    print("Workflow Execution:")
    for result in results:
        print(f"  Task {result.task_id}: {result.status.value} (Agent: {result.agent_id})")

    # Test message bus
    print("\n[5] Inter-Agent Message Bus")
    print("-" * 40)
    message_bus = MessageBus()

    message_bus.subscribe("worker-1", "data-ready")
    message_bus.subscribe("specialist-1", "data-ready")

    message_bus.publish("worker-1", "data-ready", {"data": "processed", "count": 100})

    print("Published message to 'data-ready' channel")
    print(f"Subscribers: worker-1, specialist-1")
    print(f"Messages sent: {len(message_bus.messages)}")

    print("\n" + "=" * 60)
    print("Advanced Agent Orchestration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())