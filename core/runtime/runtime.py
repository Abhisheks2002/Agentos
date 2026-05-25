"""Agent Runtime Engine - Core execution engine for AI agents."""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import logging

from ..models.models import Agent, AgentStatus, AgentType, Task

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of agent execution."""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class AgentRuntime:
    """
    Core agent runtime engine.
    Manages agent lifecycle, execution, and task scheduling.
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._executor_plugins: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}

    # --- Agent Management ---

    async def create_agent(
        self,
        name: str,
        agent_type: AgentType = AgentType.CHAT,
        description: str = None,
        config: Dict[str, Any] = None,
        tools: List[str] = None
    ) -> Agent:
        """Create a new agent."""
        agent = Agent(
            id=f"agent_{uuid.uuid4().hex[:12]}",
            name=name,
            type=agent_type,
            description=description,
            config=config or {},
            tools=tools or [],
            status=AgentStatus.CREATED
        )
        self.agents[agent.id] = agent
        logger.info(f"Created agent: {agent.id} - {name}")
        await self._emit_event("agent_created", {"agent": agent})
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    async def list_agents(self, status: AgentStatus = None) -> List[Agent]:
        """List all agents, optionally filtered by status."""
        agents = list(self.agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents

    async def update_agent(self, agent_id: str, **kwargs) -> Optional[Agent]:
        """Update agent configuration."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        agent.updated_at = datetime.now()
        await self._emit_event("agent_updated", {"agent": agent})
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Deleted agent: {agent_id}")
            await self._emit_event("agent_deleted", {"agent_id": agent_id})
            return True
        return False

    # --- Task Execution ---

    async def create_task(
        self,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> Task:
        """Create a new task for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        task = Task(
            id=f"task_{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            input_data=input_data,
            status="pending"
        )
        self.tasks[task.id] = task
        await self.task_queue.put(task)
        logger.info(f"Created task: {task.id} for agent {agent_id}")
        return task

    async def execute_task(self, task_id: str) -> ExecutionResult:
        """Execute a task synchronously."""
        task = self.tasks.get(task_id)
        if not task:
            return ExecutionResult(success=False, error="Task not found")

        agent = self.agents.get(task.agent_id)
        if not agent:
            return ExecutionResult(success=False, error="Agent not found")

        # Update task status
        task.status = "running"
        task.started_at = datetime.now()
        agent.status = AgentStatus.RUNNING

        try:
            # Execute based on agent type
            if agent.type == AgentType.CHAT:
                result = await self._execute_chat(agent, task.input_data)
            elif agent.type == AgentType.WORKFLOW:
                result = await self._execute_workflow(agent, task.input_data)
            elif agent.type == AgentType.AUTONOMOUS:
                result = await self._execute_autonomous(agent, task.input_data)
            elif agent.type == AgentType.ORCHESTRATOR:
                result = await self._execute_orchestrator(agent, task.input_data)
            else:
                result = await self._execute_default(agent, task.input_data)

            # Update task with result
            task.output_data = result.data
            task.status = "completed" if result.success else "failed"
            task.completed_at = datetime.now()
            agent.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED

            if result.error:
                task.error = result.error

            await self._emit_event("task_completed", {"task": task, "result": result})
            return result

        except Exception as e:
            logger.exception(f"Task execution failed: {task_id}")
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            agent.status = AgentStatus.FAILED
            return ExecutionResult(success=False, error=str(e))

    async def run_task_async(self, task_id: str) -> asyncio.Task:
        """Run a task asynchronously."""
        if task_id in self.running_tasks:
            raise ValueError(f"Task {task_id} is already running")

        async_task = asyncio.create_task(self.execute_task(task_id))
        self.running_tasks[task_id] = async_task

        # Clean up when done
        async_task.add_done_callback(
            lambda t: self.running_tasks.pop(task_id, None)
        )
        return async_task

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get task status."""
        return self.tasks.get(task_id)

    # --- Agent Type Executors ---

    async def _execute_chat(
        self,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a chat agent."""
        message = input_data.get("message", "")
        context = input_data.get("context", {})

        # Placeholder for LLM execution
        # In production, this would integrate with LangChain/LangGraph
        response = {
            "reply": f"Agent {agent.name} received: {message}",
            "agent_id": agent.id,
            "context": context
        }

        logger.info(f"Chat agent {agent.id} executed")
        return ExecutionResult(success=True, data=response)

    async def _execute_workflow(
        self,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a workflow agent."""
        workflow_steps = agent.config.get("steps", [])

        results = []
        for i, step in enumerate(workflow_steps):
            step_result = {
                "step": i + 1,
                "name": step.get("name"),
                "status": "completed"
            }
            results.append(step_result)

        return ExecutionResult(
            success=True,
            data={"steps": results, "agent_id": agent.id}
        )

    async def _execute_autonomous(
        self,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute an autonomous agent."""
        goal = input_data.get("goal", "")

        # Autonomous agents would use planning + execution loops
        response = {
            "goal": goal,
            "status": "autonomous_execution",
            "agent_id": agent.id,
            "actions_taken": []
        }

        return ExecutionResult(success=True, data=response)

    async def _execute_orchestrator(
        self,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute an orchestrator agent."""
        sub_agents = input_data.get("sub_agents", [])

        # Coordinate multiple agents
        results = []
        for sub_agent_id in sub_agents:
            results.append({
                "sub_agent_id": sub_agent_id,
                "status": "coordinated"
            })

        return ExecutionResult(
            success=True,
            data={"sub_agents": results, "agent_id": agent.id}
        )

    async def _execute_default(
        self,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Default execution fallback."""
        return ExecutionResult(
            success=True,
            data={"agent_id": agent.id, "input": input_data}
        )

    # --- Plugin System ---

    def register_executor(self, name: str, executor: Callable):
        """Register a custom executor plugin."""
        self._executor_plugins[name] = executor
        logger.info(f"Registered executor plugin: {name}")

    async def execute_with_plugin(
        self,
        plugin_name: str,
        agent: Agent,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute using a registered plugin."""
        executor = self._executor_plugins.get(plugin_name)
        if not executor:
            return ExecutionResult(
                success=False,
                error=f"Plugin {plugin_name} not found"
            )

        try:
            result = await executor(agent, input_data)
            return ExecutionResult(success=True, data=result)
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    # --- Event System ---

    def on(self, event: str, handler: Callable):
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _emit_event(self, event: str, data: Dict):
        """Emit an event to all handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")


# Global runtime instance
_runtime: Optional[AgentRuntime] = None


def get_runtime() -> AgentRuntime:
    """Get the global runtime instance."""
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime
