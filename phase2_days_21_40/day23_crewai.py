"""
Day 23: CrewAI - Multi-Agent Teams
===================================
Skill: Multi-Agent Orchestration
Mini Project: Research Team Crew

CrewAI enables coordination of multiple AI agents working together
on complex tasks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class AgentRole(str, Enum):
    """Predefined agent roles"""
    RESEARCHER = "researcher"
    WRITER = "writer"
    ANALYST = "analyst"
    EDITOR = "editor"
    COORDINATOR = "coordinator"


@dataclass
class Task:
    """A task in the crew"""
    id: str
    description: str
    agent_role: AgentRole
    status: str = "pending"
    result: Any = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        self.id = f"task_{uuid.uuid4().hex[:8]}"


@dataclass
class CrewAgent:
    """A crew member agent"""
    id: str
    name: str
    role: AgentRole
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 5

    def __post_init__(self):
        self.id = f"agent_{uuid.uuid4().hex[:8]}"
        self._tasks_completed = 0

    def can_handle(self, task: Task) -> bool:
        """Check if agent can handle this task"""
        return task.agent_role == self.role

    def complete_task(self, task: Task, result: Any) -> bool:
        """Mark task as completed"""
        if self._tasks_completed < self.max_iterations:
            task.result = result
            task.status = "completed"
            self._tasks_completed += 1
            return True
        return False


class CrewProcess(str, Enum):
    """Crew execution processes"""
    SEQUENTIAL = "sequential"  # One after another
    HIERARCHICAL = "hierarchical"  # Manager -> workers
    PARALLEL = "parallel"  # All at once


class Crew:
    """
    Crew - Multi-agent team
    ========================

    Orchestrates multiple agents to complete complex tasks
    """

    def __init__(
        self,
        name: str,
        agents: List[CrewAgent],
        process: CrewProcess = CrewProcess.SEQUENTIAL,
        verbose: bool = True
    ):
        self.name = name
        self.agents = agents
        self.process = process
        self.verbose = verbose
        self.tasks: List[Task] = []
        self.execution_log: List[Dict[str, Any]] = []

    def add_task(self, description: str, role: AgentRole) -> Task:
        """Add a task to the crew"""
        task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            description=description,
            agent_role=role
        )
        self.tasks.append(task)
        return task

    async def execute(self, kickoff_input: Any = None) -> Dict[str, Any]:
        """Execute all tasks"""
        results = {}
        start_time = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Crew: {self.name}")
            print(f"Process: {self.process.value}")
            print(f"Agents: {len(self.agents)}")
            print(f"Tasks: {len(self.tasks)}")
            print(f"{'='*60}\n")

        if self.process == CrewProcess.SEQUENTIAL:
            results = await self._execute_sequential(kickoff_input)
        elif self.process == CrewProcess.HIERARCHICAL:
            results = await self._execute_hierarchical(kickoff_input)
        elif self.process == CrewProcess.PARALLEL:
            results = await self._execute_parallel(kickoff_input)

        end_time = datetime.now()

        return {
            "crew": self.name,
            "results": results,
            "duration": (end_time - start_time).total_seconds(),
            "tasks_completed": len([t for t in self.tasks if t.status == "completed"])
        }

    async def _execute_sequential(self, kickoff_input: Any) -> Dict[str, Any]:
        """Execute tasks sequentially"""
        results = {}
        prev_result = kickoff_input

        for task in self.tasks:
            # Find agent for task
            agent = self._find_agent(task)

            if not agent:
                if self.verbose:
                    print(f"  ⚠ No agent for task: {task.description}")
                continue

            if self.verbose:
                print(f"  → {agent.name} ({agent.role.value}): {task.description}")

            # Execute task (simulated)
            result = await self._execute_task(agent, task, prev_result)

            # Store result
            prev_result = result
            results[task.id] = {
                "task": task.description,
                "agent": agent.name,
                "result": result
            }

            # Log
            self.execution_log.append({
                "task_id": task.id,
                "agent_id": agent.id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        return results

    async def _execute_hierarchical(self, kickoff_input: Any) -> Dict[str, Any]:
        """Execute with hierarchical structure (manager + workers)"""
        # Find coordinator
        coordinator = next(
            (a for a in self.agents if a.role == AgentRole.COORDINATOR),
            self.agents[0]
        )

        if self.verbose:
            print(f"  👔 Coordinator: {coordinator.name}")

        # Assign tasks to workers
        worker_tasks = []
        for task in self.tasks:
            agent = self._find_agent(task)
            if agent and agent != coordinator:
                worker_tasks.append((agent, task))

        # Execute in parallel
        results = {}
        for agent, task in worker_tasks:
            if self.verbose:
                print(f"  → {agent.name}: {task.description}")

            result = await self._execute_task(agent, task, kickoff_input)
            results[task.id] = {
                "task": task.description,
                "agent": agent.name,
                "result": result
            }

        # Coordinator reviews
        if self.verbose:
            print(f"  👔 {coordinator.name} reviewing results...")

        return results

    async def _execute_parallel(self, kickoff_input: Any) -> Dict[str, Any]:
        """Execute all tasks in parallel"""
        results = {}

        # Assign tasks to agents
        task_assignments = []
        for task in self.tasks:
            agent = self._find_agent(task)
            if agent:
                task_assignments.append((agent, task))

        # Execute all
        for agent, task in task_assignments:
            if self.verbose:
                print(f"  → {agent.name}: {task.description}")

            result = await self._execute_task(agent, task, kickoff_input)
            results[task.id] = {
                "task": task.description,
                "agent": agent.name,
                "result": result
            }

        return results

    def _find_agent(self, task: Task) -> Optional[CrewAgent]:
        """Find best agent for task"""
        for agent in self.agents:
            if agent.can_handle(task):
                return agent
        return self.agents[0] if self.agents else None

    async def _execute_task(self, agent: CrewAgent, task: Task, context: Any) -> Any:
        """Execute a single task"""
        # Simulate work
        result = f"[{agent.name}] Completed: {task.description[:30]}..."

        agent.complete_task(task, result)
        task.status = "completed"

        return result


# Predefined agent factory
class AgentFactory:
    """Factory for creating crew agents"""

    @staticmethod
    def create_researcher(name: str = "Researcher") -> CrewAgent:
        return CrewAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            name=name,
            role=AgentRole.RESEARCHER,
            skills=["web_search", "data_collection", "analysis"],
            tools=["search", "scrape", "analyze"]
        )

    @staticmethod
    def create_writer(name: str = "Writer") -> CrewAgent:
        return CrewAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            name=name,
            role=AgentRole.WRITER,
            skills=["writing", "summarization", "editing"],
            tools=["write", "summarize"]
        )

    @staticmethod
    def create_analyst(name: str = "Analyst") -> CrewAgent:
        return CrewAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            name=name,
            role=AgentRole.ANALYST,
            skills=["data_analysis", "statistics", "reporting"],
            tools=["analyze", "calculate", "report"]
        )

    @staticmethod
    def create_coordinator(name: str = "Coordinator") -> CrewAgent:
        return CrewAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            name=name,
            role=AgentRole.COORDINATOR,
            skills=["planning", "delegation", "oversight"],
            tools=["plan", "delegate", "monitor"]
        )


# Demo
def run_demo():
    print("=" * 70)
    print("CrewAI - Multi-Agent Teams Demo")
    print("=" * 70)

    # Create agents
    print("\n[1] Creating Research Team")
    print("-" * 40)

    researcher = AgentFactory.create_researcher("Alex")
    writer = AgentFactory.create_writer("Jordan")
    analyst = AgentFactory.create_analyst("Sam")

    print(f"  ✓ {researcher.name} ({researcher.role.value})")
    print(f"  ✓ {writer.name} ({writer.role.value})")
    print(f"  ✓ {analyst.name} ({analyst.role.value})")

    # Create crew
    print("\n[2] Creating Crew")
    print("-" * 40)

    crew = Crew(
        name="Research Team",
        agents=[researcher, writer, analyst],
        process=CrewProcess.SEQUENTIAL,
        verbose=True
    )

    # Add tasks
    crew.add_task("Research latest AI trends", AgentRole.RESEARCHER)
    crew.add_task("Write summary report", AgentRole.WRITER)
    crew.add_task("Analyze data findings", AgentRole.ANALYST)

    print(f"  ✓ Added 3 tasks")

    # Execute
    import asyncio

    print("\n[3] Executing Crew")
    print("-" * 40)

    result = asyncio.run(crew.execute("AI trends research"))

    print(f"\n{'='*60}")
    print(f"Crew completed!")
    print(f"  Duration: {result['duration']:.2f}s")
    print(f"  Tasks: {result['tasks_completed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_demo()