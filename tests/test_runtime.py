"""Tests for AgentOS Runtime."""

import pytest
import asyncio
from core.runtime.runtime import AgentRuntime
from core.models.models import AgentType, AgentStatus


@pytest.fixture
def runtime():
    """Create a runtime instance."""
    return AgentRuntime()


@pytest.mark.asyncio
async def test_create_agent(runtime):
    """Test agent creation."""
    agent = await runtime.create_agent(
        name="Test Agent",
        agent_type=AgentType.CHAT,
        description="A test agent"
    )

    assert agent.name == "Test Agent"
    assert agent.type == AgentType.CHAT
    assert agent.status == AgentStatus.CREATED
    assert agent.id.startswith("agent_")


@pytest.mark.asyncio
async def test_get_agent(runtime):
    """Test getting an agent."""
    agent = await runtime.create_agent(name="Test Agent")
    retrieved = await runtime.get_agent(agent.id)

    assert retrieved is not None
    assert retrieved.id == agent.id
    assert retrieved.name == "Test Agent"


@pytest.mark.asyncio
async def test_list_agents(runtime):
    """Test listing agents."""
    await runtime.create_agent(name="Agent 1")
    await runtime.create_agent(name="Agent 2")

    agents = await runtime.list_agents()
    assert len(agents) >= 2


@pytest.mark.asyncio
async def test_create_task(runtime):
    """Test task creation."""
    agent = await runtime.create_agent(name="Test Agent")
    task = await runtime.create_task(
        agent_id=agent.id,
        input_data={"message": "Hello"}
    )

    assert task.agent_id == agent.id
    assert task.status == "pending"


@pytest.mark.asyncio
async def test_execute_task(runtime):
    """Test task execution."""
    agent = await runtime.create_agent(name="Test Agent")
    task = await runtime.create_task(
        agent_id=agent.id,
        input_data={"message": "Hello"}
    )

    result = await runtime.execute_task(task.id)

    assert result.success is True
    assert result.data is not None


@pytest.mark.asyncio
async def test_delete_agent(runtime):
    """Test agent deletion."""
    agent = await runtime.create_agent(name="Test Agent")
    success = await runtime.delete_agent(agent.id)

    assert success is True
    assert await runtime.get_agent(agent.id) is None


@pytest.mark.asyncio
async def test_agent_types(runtime):
    """Test different agent types."""
    chat = await runtime.create_agent(name="Chat Agent", agent_type=AgentType.CHAT)
    workflow = await runtime.create_agent(name="Workflow Agent", agent_type=AgentType.WORKFLOW)
    autonomous = await runtime.create_agent(name="Auto Agent", agent_type=AgentType.AUTONOMOUS)

    assert chat.type == AgentType.CHAT
    assert workflow.type == AgentType.WORKFLOW
    assert autonomous.type == AgentType.AUTONOMOUS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
