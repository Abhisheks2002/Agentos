"""Tests for AgentOS core components."""

import pytest
import asyncio
from core.models.models import Agent, AgentType, AgentStatus
from core.runtime.runtime import AgentRuntime
from core.memory.memory import MemoryManager, VectorStore
from core.tools.registry import ToolRegistry, ToolType
from core.governance.governance import GovernanceEngine, Permission


class TestAgentRuntime:
    """Test Agent Runtime."""

    @pytest.fixture
    def runtime(self):
        return AgentRuntime()

    @pytest.mark.asyncio
    async def test_create_agent(self, runtime):
        """Test agent creation."""
        agent = await runtime.create_agent(
            name="Test Agent",
            agent_type=AgentType.CHAT,
            description="A test agent"
        )

        assert agent.name == "Test Agent"
        assert agent.type == AgentType.CHAT
        assert agent.status == AgentStatus.CREATED

    @pytest.mark.asyncio
    async def test_get_agent(self, runtime):
        """Test getting an agent."""
        agent = await runtime.create_agent(name="Test Agent")
        retrieved = await runtime.get_agent(agent.id)

        assert retrieved is not None
        assert retrieved.id == agent.id
        assert retrieved.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_list_agents(self, runtime):
        """Test listing agents."""
        await runtime.create_agent(name="Agent 1")
        await runtime.create_agent(name="Agent 2")

        agents = await runtime.list_agents()
        assert len(agents) >= 2

    @pytest.mark.asyncio
    async def test_execute_task(self, runtime):
        """Test task execution."""
        agent = await runtime.create_agent(
            name="Test Agent",
            agent_type=AgentType.CHAT
        )

        task = await runtime.create_task(
            agent_id=agent.id,
            input_data={"message": "Hello"}
        )

        result = await runtime.execute_task(task.id)

        assert result.success is True
        assert result.data is not None


class TestMemoryManager:
    """Test Memory Manager."""

    @pytest.fixture
    def memory(self):
        return MemoryManager()

    @pytest.mark.asyncio
    async def test_add_short_term_memory(self, memory):
        """Test adding short-term memory."""
        memory_id = await memory.add_short_term(
            agent_id="test_agent",
            content="Test memory content"
        )

        assert memory_id is not None

    @pytest.mark.asyncio
    async def test_get_short_term_memory(self, memory):
        """Test getting short-term memory."""
        await memory.add_short_term(
            agent_id="test_agent",
            content="Memory 1"
        )
        await memory.add_short_term(
            agent_id="test_agent",
            content="Memory 2"
        )

        memories = await memory.get_short_term("test_agent")
        assert len(memories) >= 2

    @pytest.mark.asyncio
    async def test_search_memory(self, memory):
        """Test semantic search."""
        await memory.add_long_term(
            agent_id="test_agent",
            content="Python is a programming language"
        )
        await memory.add_long_term(
            agent_id="test_agent",
            content="JavaScript is for web development"
        )

        results = await memory.search(
            agent_id="test_agent",
            query="programming",
            limit=5
        )

        assert isinstance(results, list)


class TestToolRegistry:
    """Test Tool Registry."""

    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    @pytest.mark.asyncio
    async def test_register_tool(self, registry):
        """Test tool registration."""
        async def mock_executor(params, context):
            return {"result": "success"}

        tool = await registry.register_tool(
            name="test_tool",
            tool_type=ToolType.CUSTOM,
            description="A test tool",
            executor=mock_executor
        )

        assert tool.name == "test_tool"
        assert tool.enabled is True

    @pytest.mark.asyncio
    async def test_execute_tool(self, registry):
        """Test tool execution."""
        async def mock_executor(params, context):
            return {"input": params.get("value")}

        await registry.register_tool(
            name="echo",
            executor=mock_executor
        )

        result = await registry.execute(
            tool_name="echo",
            parameters={"value": "test"}
        )

        assert result["success"] is True


class TestGovernanceEngine:
    """Test Governance Engine."""

    @pytest.fixture
    def governance(self):
        return GovernanceEngine()

    @pytest.mark.asyncio
    async def test_create_user(self, governance):
        """Test user creation."""
        user = await governance.create_user(
            username="testuser",
            email="test@example.com"
        )

        assert user.username == "testuser"
        assert user.role == "user"

    @pytest.mark.asyncio
    async def test_check_permission(self, governance):
        """Test permission checking."""
        user = await governance.create_user(username="admin", role="admin")

        has_permission = await governance.check_permission(
            user.id,
            Permission.AGENT_CREATE
        )

        assert has_permission is True

    @pytest.mark.asyncio
    async def test_audit_log(self, governance):
        """Test audit logging."""
        user = await governance.create_user(username="testuser")

        await governance.check_permission(user.id, Permission.AGENT_READ)

        logs = await governance.get_audit_logs(user_id=user.id)
        assert len(logs) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
