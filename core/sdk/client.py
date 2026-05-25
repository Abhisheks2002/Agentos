"""SDK - Developer SDK for AgentOS."""

import asyncio
from typing import Any, Dict, List, Optional
import logging

from .runtime.runtime import AgentRuntime, get_runtime
from .memory.memory import MemoryManager, get_memory_manager
from .tools.registry import ToolRegistry, get_tool_registry
from .governance.governance import GovernanceEngine, get_governance_engine, Permission

logger = logging.getLogger(__name__)


class AgentOSClient:
    """
    Main client for interacting with AgentOS.
    Provides a simple API for developers.
    """

    def __init__(
        self,
        api_url: str = None,
        api_key: str = None
    ):
        self.api_url = api_url
        self.api_key = api_key

        # Use local mode if no API URL
        self.local_mode = api_url is None

        if self.local_mode:
            self.runtime = get_runtime()
            self.memory = get_memory_manager()
            self.tools = get_tool_registry()
            self.governance = get_governance_engine()

    # --- Agent Operations ---

    async def create_agent(
        self,
        name: str,
        agent_type: str = "chat",
        description: str = None,
        config: Dict = None,
        tools: List[str] = None
    ):
        """Create a new agent."""
        from ..models.models import AgentType

        type_map = {
            "chat": AgentType.CHAT,
            "workflow": AgentType.WORKFLOW,
            "autonomous": AgentType.AUTONOMOUS,
            "orchestrator": AgentType.ORCHESTRATOR
        }

        return await self.runtime.create_agent(
            name=name,
            agent_type=type_map.get(agent_type, AgentType.CHAT),
            description=description,
            config=config,
            tools=tools
        )

    async def run_agent(
        self,
        agent_id: str,
        message: str = None,
        **kwargs
    ):
        """Run an agent with input data."""
        input_data = kwargs
        if message:
            input_data["message"] = message

        task = await self.runtime.create_task(
            agent_id=agent_id,
            input_data=input_data
        )

        result = await self.runtime.execute_task(task.id)
        return result

    async def get_agent(self, agent_id: str):
        """Get an agent by ID."""
        return await self.runtime.get_agent(agent_id)

    async def list_agents(self):
        """List all agents."""
        return await self.runtime.list_agents()

    async def delete_agent(self, agent_id: str):
        """Delete an agent."""
        return await self.runtime.delete_agent(agent_id)

    # --- Memory Operations ---

    async def remember(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "short_term",
        metadata: Dict = None
    ):
        """Store a memory."""
        if memory_type == "short_term":
            return await self.memory.add_short_term(agent_id, content, metadata)
        elif memory_type == "long_term":
            return await self.memory.add_long_term(agent_id, content, metadata)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

    async def recall(
        self,
        agent_id: str,
        query: str = None,
        memory_type: str = "short_term",
        limit: int = 10
    ):
        """Retrieve memories."""
        if query:
            return await self.memory.search(agent_id, query, limit, memory_type)
        else:
            if memory_type == "short_term":
                return await self.memory.get_short_term(agent_id, limit)
            elif memory_type == "long_term":
                return await self.memory.get_long_term(agent_id, limit)

    # --- Tool Operations ---

    async def register_tool(
        self,
        name: str,
        executor,
        description: str = None,
        schema: Dict = None
    ):
        """Register a custom tool."""
        return await self.tools.register_tool(
            name=name,
            executor=executor,
            description=description,
            schema=schema
        )

    async def use_tool(
        self,
        tool_name: str,
        parameters: Dict = None,
        context: Dict = None
    ):
        """Use a tool."""
        return await self.tools.execute(tool_name, parameters, context)

    async def list_tools(self):
        """List available tools."""
        return await self.tools.list_tools()

    # --- Workflow Operations ---

    async def create_workflow(self, name: str, steps: List[Dict]):
        """Create a workflow."""
        from ..models.models import Workflow

        workflow = Workflow(
            name=name,
            steps=steps
        )
        return workflow

    async def run_workflow(self, workflow, input_data: Dict):
        """Run a workflow."""
        results = []
        for step in workflow.steps:
            step_name = step.get("name")
            tool = step.get("tool")
            params = step.get("params", {})

            # Execute tool
            result = await self.use_tool(tool, params, input_data)
            results.append({
                "step": step_name,
                "result": result
            })

            # Update context
            input_data.update(result.get("result", {}))

        return results


class AgentBuilder:
    """Builder for creating agents with fluent API."""

    def __init__(self, client: AgentOSClient):
        self.client = client
        self._name = None
        self._type = "chat"
        self._description = None
        self._config = {}
        self._tools = []

    def name(self, name: str):
        self._name = name
        return self

    def type(self, agent_type: str):
        self._type = agent_type
        return self

    def description(self, description: str):
        self._description = description
        return self

    def config(self, **kwargs):
        self._config.update(kwargs)
        return self

    def tool(self, tool_name: str):
        self._tools.append(tool_name)
        return self

    async def create(self):
        """Create the agent."""
        if not self._name:
            raise ValueError("Agent name is required")

        return await self.client.create_agent(
            name=self._name,
            agent_type=self._type,
            description=self._description,
            config=self._config,
            tools=self._tools
        )


# --- Convenience Functions ---

_client: Optional[AgentOSClient] = None


def get_client(api_url: str = None, api_key: str = None) -> AgentOSClient:
    """Get a global AgentOS client."""
    global _client
    if _client is None:
        _client = AgentOSClient(api_url, api_key)
    return _client


async def create_agent(name: str, **kwargs) -> Any:
    """Quick helper to create an agent."""
    client = get_client()
    return await client.create_agent(name, **kwargs)


async def run(agent_id: str, message: str = None, **kwargs) -> Any:
    """Quick helper to run an agent."""
    client = get_client()
    return await client.run_agent(agent_id, message, **kwargs)


async def remember(agent_id: str, content: str, **kwargs) -> str:
    """Quick helper to store memory."""
    client = get_client()
    return await client.remember(agent_id, content, **kwargs)


async def recall(agent_id: str, query: str = None, **kwargs) -> Any:
    """Quick helper to retrieve memory."""
    client = get_client()
    return await client.recall(agent_id, query, **kwargs)
