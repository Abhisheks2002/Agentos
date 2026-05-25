"""
Day 86: Agent Orchestration Patterns
====================================

Advanced orchestration patterns for coordinating multiple agents,
including hierarchical, sequential, parallel, and dynamic orchestration.

Key Concepts:
- Hierarchical Orchestration
- Sequential & Parallel Execution
- Dynamic Task Distribution
- Load Balancing Across Agents
- Fault-Tolerant Orchestration
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
from collections import defaultdict
import heapq
import random


class OrchestrationMode(Enum):
    """Orchestration execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    DYNAMIC = "dynamic"
    FANOUT_FANIN = "fanout_fanin"


class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    BUSY = "busy"
    FAULT = "fault"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Agent:
    """Represents an agent in the orchestration"""
    agent_id: str
    name: str
    capabilities: List[str]
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    status: AgentStatus = AgentStatus.IDLE
    performance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_accept_task(self) -> bool:
        """Check if agent can accept more tasks"""
        return (
            self.status == AgentStatus.IDLE and
            self.current_tasks < self.max_concurrent_tasks
        )


@dataclass
class Task:
    """Represents a task to be executed by agents"""
    task_id: str
    name: str
    description: str
    required_capabilities: List[str]
    input_data: Any
    priority: int = 0
    timeout: float = 300.0
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __lt__(self, other):
        """Priority queue comparison"""
        return self.priority > other.priority


@dataclass
class OrchestrationResult:
    """Result of orchestration execution"""
    orchestration_id: str
    mode: OrchestrationMode
    tasks: List[Task]
    total_duration: float
    success_count: int
    failure_count: int
    agent_assignments: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SequentialOrchestrator:
    """Sequential task execution - one task at a time"""

    def __init__(self):
        self.execution_history: List[Dict] = []

    async def execute(
        self,
        tasks: List[Task],
        agents: List[Agent],
        executor: Callable[[Task, Agent], Any]
    ) -> OrchestrationResult:
        """Execute tasks sequentially"""
        start_time = datetime.now()
        orchestration_id = str(uuid.uuid4())[:8]

        agent = agents[0]  # Use first available agent
        assignments = {}

        for task in tasks:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.assigned_agent = agent.agent_id

            try:
                # Simulate task execution
                await asyncio.sleep(0.1)
                task.result = await executor(task, agent)
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

            task.completed_at = datetime.now()
            assignments[task.task_id] = agent.agent_id

        duration = (datetime.now() - start_time).total_seconds()
        success = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        return OrchestrationResult(
            orchestration_id=orchestration_id,
            mode=OrchestrationMode.SEQUENTIAL,
            tasks=tasks,
            total_duration=duration,
            success_count=success,
            failure_count=len(tasks) - success,
            agent_assignments=assignments
        )


class ParallelOrchestrator:
    """Parallel task execution - multiple tasks simultaneously"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent

    async def execute(
        self,
        tasks: List[Task],
        agents: List[Agent],
        executor: Callable[[Task, Agent], Any]
    ) -> OrchestrationResult:
        """Execute tasks in parallel with concurrency limit"""
        start_time = datetime.now()
        orchestration_id = str(uuid.uuid4())[:8]

        assignments = {}
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_with_limit(task: Task, agent: Agent):
            async with semaphore:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                task.assigned_agent = agent.agent_id
                assignments[task.task_id] = agent.agent_id

                try:
                    await asyncio.sleep(0.1)
                    task.result = await executor(task, agent)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                finally:
                    task.completed_at = datetime.now()

        # Create coroutines
        coroutines = []
        for task in tasks:
            agent = self._select_agent(agents, task)
            if agent:
                coroutines.append(execute_with_limit(task, agent))

        # Execute all concurrently
        await asyncio.gather(*coroutines, return_exceptions=True)

        duration = (datetime.now() - start_time).total_seconds()
        success = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        return OrchestrationResult(
            orchestration_id=orchestration_id,
            mode=OrchestrationMode.PARALLEL,
            tasks=tasks,
            total_duration=duration,
            success_count=success,
            failure_count=len(tasks) - success,
            agent_assignments=assignments
        )

    def _select_agent(self, agents: List[Agent], task: Task) -> Optional[Agent]:
        """Select best agent for task based on capabilities"""
        capable = [a for a in agents if a.can_accept_task()]
        if not capable:
            return None

        # Select agent with matching capabilities and best performance
        matching = [a for a in capable if any(c in a.capabilities for c in task.required_capabilities)]
        if not matching:
            matching = capable

        return max(matching, key=lambda a: a.performance_score)


class HierarchicalOrchestrator:
    """Hierarchical orchestration - supervisor agents manage sub-agents"""

    def __init__(self):
        self.supervisor_tasks: Dict[str, List[Task]] = defaultdict(list)

    async def execute(
        self,
        tasks: List[Task],
        supervisors: List[Agent],
        workers: List[Agent],
        executor: Callable[[Task, Agent], Any]
    ) -> OrchestrationResult:
        """Execute tasks hierarchically with supervisors"""
        start_time = datetime.now()
        orchestration_id = str(uuid.uuid4())[:8]

        # Group tasks by priority for supervisor assignment
        task_groups = defaultdict(list)
        for task in tasks:
            priority_group = task.priority // 10
            task_groups[priority_group].append(task)

        assignments = {}
        worker_pool = list(workers)

        for group_id, group_tasks in task_groups.items():
            if not supervisor := supervisors[group_id % len(supervisors)]:
                continue

            # Supervisor manages this group
            for task in group_tasks:
                if not worker_pool:
                    worker_pool = list(workers)

                worker = worker_pool.pop(0)
                task.assigned_agent = worker.agent_id
                assignments[task.task_id] = worker.agent_id

                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

                try:
                    await asyncio.sleep(0.1)
                    task.result = await executor(task, worker)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                finally:
                    task.completed_at = datetime.now()

        duration = (datetime.now() - start_time).total_seconds()
        success = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        return OrchestrationResult(
            orchestration_id=orchestration_id,
            mode=OrchestrationMode.HIERARCHICAL,
            tasks=tasks,
            total_duration=duration,
            success_count=success,
            failure_count=len(tasks) - success,
            agent_assignments=assignments,
            metadata={"supervisors_used": len(supervisors)}
        )


class DynamicOrchestrator:
    """Dynamic orchestration - intelligent task distribution based on load"""

    def __init__(self):
        self.load_history: Dict[str, List[float]] = defaultdict(list)

    async def execute(
        self,
        tasks: List[Task],
        agents: List[Agent],
        executor: Callable[[Task, Agent], Any]
    ) -> OrchestrationResult:
        """Execute tasks with dynamic load balancing"""
        start_time = datetime.now()
        orchestration_id = str(uuid.uuid4())[:8]

        # Priority queue for tasks
        task_queue = list(tasks)
        heapq.heapify(task_queue)

        assignments = {}
        active_tasks: Dict[str, asyncio.Task] = {}
        available_agents = list(agents)

        while task_queue or active_tasks:
            # Find completed tasks
            done = [tid for tid, t in active_tasks.items() if t.done()]
            for tid in done:
                task = next(t for t in tasks if t.task_id == tid)
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.COMPLETED
                del active_tasks[tid]

                # Return agent to pool
                if task.assigned_agent:
                    available_agents.append(
                        next(a for a in agents if a.agent_id == task.assigned_agent)
                    )

            # Assign new tasks if agents available
            while task_queue and available_agents:
                task = heapq.heappop(task_queue)
                agent = self._select_best_agent(available_agents, task)

                if agent:
                    available_agents.remove(agent)
                    task.assigned_agent = agent.agent_id
                    assignments[task.task_id] = agent.agent_id

                    # Start execution
                    async def run_task(t: Task, a: Agent):
                        t.status = TaskStatus.RUNNING
                        t.started_at = datetime.now()
                        try:
                            await asyncio.sleep(0.1)
                            t.result = await executor(t, a)
                            t.status = TaskStatus.COMPLETED
                        except Exception as e:
                            t.status = TaskStatus.FAILED
                            t.error = str(e)
                        finally:
                            t.completed_at = datetime.now()

                    active_tasks[task.task_id] = asyncio.create_task(run_task(task, agent))

            await asyncio.sleep(0.01)

        duration = (datetime.now() - start_time).total_seconds()
        success = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        return OrchestrationResult(
            orchestration_id=orchestration_id,
            mode=OrchestrationMode.DYNAMIC,
            tasks=tasks,
            total_duration=duration,
            success_count=success,
            failure_count=len(tasks) - success,
            agent_assignments=assignments
        )

    def _select_best_agent(self, agents: List[Agent], task: Task) -> Optional[Agent]:
        """Select best agent based on current load and capabilities"""
        capable = [a for a in agents if a.can_accept_task()]
        if not capable:
            return None

        # Filter by capabilities
        matching = [a for a in capable if any(c in a.capabilities for c in task.required_capabilities)]
        if not matching:
            matching = capable

        # Select agent with lowest current load and best performance
        return min(matching, key=lambda a: (a.current_tasks, -a.performance_score))


class FanoutFaninOrchestrator:
    """Fan-out/Fan-in orchestration - distribute, then aggregate"""

    def __init__(self, fanout_size: int = 5):
        self.fanout_size = fanout_size

    async def execute(
        self,
        tasks: List[Task],
        agents: List[Agent],
        executor: Callable[[Task, Agent], Any],
        aggregator: Callable[[List[Task]], Any]
    ) -> OrchestrationResult:
        """Execute tasks with fan-out/fan-in pattern"""
        start_time = datetime.now()
        orchestration_id = str(uuid.uuid4())[:8]

        assignments = {}

        # Fan-out: distribute tasks to multiple agents
        fanin_results = []
        for i in range(0, len(tasks), self.fanout_size):
            fanout_tasks = tasks[i:i + self.fanout_size]

            # Execute fanout batch in parallel
            batch_coroutines = []
            for task in fanout_tasks:
                agent = self._select_agent(agents, task)
                if agent:
                    task.assigned_agent = agent.agent_id
                    assignments[task.task_id] = agent.agent_id

                    async def run_task(t: Task, a: Agent):
                        t.status = TaskStatus.RUNNING
                        t.started_at = datetime.now()
                        try:
                            await asyncio.sleep(0.1)
                            t.result = await executor(t, a)
                            t.status = TaskStatus.COMPLETED
                        except Exception as e:
                            t.status = TaskStatus.FAILED
                            t.error = str(e)
                        finally:
                            t.completed_at = datetime.now()
                            return t

                    batch_coroutines.append(run_task(task, agent))

            if batch_coroutines:
                results = await asyncio.gather(*batch_coroutines, return_exceptions=True)
                fanin_results.extend([r for r in results if isinstance(r, Task)])

        # Fan-in: aggregate results
        aggregated = await aggregator(fanin_results)

        duration = (datetime.now() - start_time).total_seconds()
        success = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        return OrchestrationResult(
            orchestration_id=orchestration_id,
            mode=OrchestrationMode.FANOUT_FANIN,
            tasks=tasks,
            total_duration=duration,
            success_count=success,
            failure_count=len(tasks) - success,
            agent_assignments=assignments,
            metadata={"aggregated_result": str(aggregated)}
        )

    def _select_agent(self, agents: List[Agent], task: Task) -> Optional[Agent]:
        """Select agent for task"""
        capable = [a for a in agents if a.can_accept_task()]
        if not capable:
            return None

        matching = [a for a in capable if any(c in a.capabilities for c in task.required_capabilities)]
        return matching[0] if matching else None


class AgentOrchestrator:
    """Main orchestrator that combines all patterns"""

    def __init__(self):
        self.sequential = SequentialOrchestrator()
        self.parallel = ParallelOrchestrator()
        self.hierarchical = HierarchicalOrchestrator()
        self.dynamic = DynamicOrchestrator()
        self.fanout_fanin = FanoutFaninOrchestrator()
        self.execution_history: List[OrchestrationResult] = []

    async def orchestrate(
        self,
        tasks: List[Task],
        agents: List[Agent],
        mode: OrchestrationMode,
        executor: Optional[Callable] = None,
        aggregator: Optional[Callable] = None
    ) -> OrchestrationResult:
        """Orchestrate tasks using specified mode"""

        # Default executor
        async def default_executor(task: Task, agent: Agent) -> Dict:
            await asyncio.sleep(random.uniform(0.1, 0.5))
            return {"status": "success", "agent": agent.name}

        # Default aggregator
        async def default_aggregator(results: List[Task]) -> Dict:
            return {"count": len(results), "results": [r.result for r in results]}

        exec_fn = executor or default_executor
        agg_fn = aggregator or default_aggregator

        # Select orchestrator based on mode
        if mode == OrchestrationMode.SEQUENTIAL:
            result = await self.sequential.execute(tasks, agents, exec_fn)
        elif mode == OrchestrationMode.PARALLEL:
            result = await self.parallel.execute(tasks, agents, exec_fn)
        elif mode == OrchestrationMode.HIERARCHICAL:
            # For hierarchical, we need supervisor and worker agents
            supervisors = [a for a in agents if "supervisor" in a.capabilities]
            workers = [a for a in agents if "worker" in a.capabilities or "supervisor" not in a.capabilities]
            if not supervisors:
                supervisors = agents[:1]
            result = await self.hierarchical.execute(tasks, supervisors, workers, exec_fn)
        elif mode == OrchestrationMode.DYNAMIC:
            result = await self.dynamic.execute(tasks, agents, exec_fn)
        elif mode == OrchestrationMode.FANOUT_FANIN:
            result = await self.fanout_fanin.execute(tasks, agents, exec_fn, agg_fn)
        else:
            result = await self.parallel.execute(tasks, agents, exec_fn)

        self.execution_history.append(result)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        if not self.execution_history:
            return {"total_orchestrations": 0}

        return {
            "total_orchestrations": len(self.execution_history),
            "by_mode": {
                mode.value: sum(1 for r in self.execution_history if r.mode == mode)
                for mode in OrchestrationMode
            },
            "average_duration": sum(r.total_duration for r in self.execution_history) / len(self.execution_history),
            "total_success": sum(r.success_count for r in self.execution_history),
            "total_failures": sum(r.failure_count for r in self.execution_history)
        }


async def simulate_task_execution(task: Task, agent: Agent) -> Dict[str, Any]:
    """Simulate task execution"""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    # Simulate success/failure
    if random.random() < 0.9:
        return {
            "status": "success",
            "agent": agent.name,
            "task": task.name,
            "output": f"Processed by {agent.name}"
        }
    else:
        raise Exception("Simulated task failure")


async def aggregate_results(tasks: List[Task]) -> Dict[str, Any]:
    """Aggregate results from multiple tasks"""
    return {
        "total_tasks": len(tasks),
        "successful": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        "results": [t.result for t in tasks if t.result]
    }


async def main():
    """Demonstrate Agent Orchestration"""
    print("=" * 60)
    print("Agent Orchestration Patterns - Day 86")
    print("=" * 60)

    # Create agents
    agents = [
        Agent(
            agent_id="agent-1",
            name="Data Agent",
            capabilities=["data-processing", "analysis"],
            max_concurrent_tasks=2,
            performance_score=0.9
        ),
        Agent(
            agent_id="agent-2",
            name="File Agent",
            capabilities=["file-operations", "data-processing"],
            max_concurrent_tasks=2,
            performance_score=0.85
        ),
        Agent(
            agent_id="agent-3",
            name="Network Agent",
            capabilities=["network", "api-calls"],
            max_concurrent_tasks=3,
            performance_score=0.95
        ),
        Agent(
            agent_id="agent-4",
            name="Compute Agent",
            capabilities=["compute", "analysis"],
            max_concurrent_tasks=1,
            performance_score=1.0
        ),
        Agent(
            agent_id="supervisor-1",
            name="Supervisor Agent",
            capabilities=["supervisor", "coordination"],
            max_concurrent_tasks=1,
            performance_score=0.92
        )
    ]

    # Create tasks
    tasks = [
        Task(
            task_id=f"task-{i}",
            name=f"Task {i}",
            description=f"Processing task {i}",
            required_capabilities=["data-processing"],
            input_data={"data": f"input-{i}"},
            priority=random.randint(1, 10)
        )
        for i in range(20)
    ]

    orchestrator = AgentOrchestrator()

    # Test different orchestration modes
    modes = [
        OrchestrationMode.SEQUENTIAL,
        OrchestrationMode.PARALLEL,
        OrchestrationMode.DYNAMIC,
        OrchestrationMode.FANOUT_FANIN
    ]

    results = {}

    for mode in modes:
        print(f"\n[Testing {mode.value} orchestration]")

        # Create fresh tasks for each mode
        test_tasks = [
            Task(
                task_id=f"{mode.value}-task-{i}",
                name=f"Task {i}",
                description=f"Task {i} for {mode.value}",
                required_capabilities=["data-processing"],
                input_data={"data": f"input-{i}"},
                priority=random.randint(1, 10)
            )
            for i in range(10)
        ]

        result = await orchestrator.orchestrate(
            test_tasks,
            agents,
            mode,
            executor=simulate_task_execution,
            aggregator=aggregate_results
        )

        results[mode.value] = result
        print(f"  Duration: {result.total_duration:.3f}s")
        print(f"  Success: {result.success_count}/{len(test_tasks)}")
        print(f"  Failures: {result.failure_count}")

    # Hierarchical test
    print(f"\n[Testing HIERARCHICAL orchestration]")

    hierarchical_tasks = [
        Task(
            task_id=f"hierarchical-task-{i}",
            name=f"Task {i}",
            description=f"Task {i}",
            required_capabilities=["worker"],
            input_data={"data": f"input-{i}"},
            priority=random.randint(1, 10)
        )
        for i in range(8)
    ]

    hierarchical_result = await orchestrator.orchestrate(
        hierarchical_tasks,
        agents,
        OrchestrationMode.HIERARCHICAL,
        executor=simulate_task_execution
    )

    print(f"  Duration: {hierarchical_result.total_duration:.3f}s")
    print(f"  Success: {hierarchical_result.success_count}/{len(hierarchical_tasks)}")

    # Statistics
    print("\n" + "=" * 60)
    print("Orchestration Statistics")
    print("=" * 60)

    stats = orchestrator.get_statistics()
    print(f"Total Orchestrations: {stats['total_orchestrations']}")
    print(f"By Mode: {stats['by_mode']}")
    print(f"Average Duration: {stats['average_duration']:.3f}s")
    print(f"Total Success: {stats['total_success']}")
    print(f"Total Failures: {stats['total_failures']}")

    print("\n" + "=" * 60)
    print("Agent Orchestration demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())