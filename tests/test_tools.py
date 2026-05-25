"""Tests for AgentOS Tools."""

import pytest
import asyncio
from core.tools.registry import ToolRegistry
from core.models.models import ToolType


@pytest.fixture
def registry():
    """Create a tool registry instance."""
    return ToolRegistry()


@pytest.fixture
async def tools(registry):
    """Register some test tools."""
    await registry.register_builtin_tools()
    return registry


@pytest.mark.asyncio
async def test_register_tool(registry):
    """Test tool registration."""

    async def dummy_executor(params, context):
        return {"result": "executed"}

    tool = await registry.register_tool(
        name="test_tool",
        tool_type=ToolType.CUSTOM,
        description="A test tool",
        executor=dummy_executor
    )

    assert tool.name == "test_tool"
    assert tool.enabled is True


@pytest.mark.asyncio
async def test_get_tool(registry):
    """Test getting a tool."""
    async def dummy_executor(params, context):
        return {"result": "executed"}

    await registry.register_tool(
        name="test_tool",
        executor=dummy_executor
    )

    tool = await registry.get_tool("test_tool")
    assert tool is not None
    assert tool.name == "test_tool"


@pytest.mark.asyncio
async def test_list_tools(registry):
    """Test listing tools."""
    async def dummy_executor(params, context):
        return {}

    await registry.register_tool(name="tool1", executor=dummy_executor)
    await registry.register_tool(name="tool2", executor=dummy_executor)

    tools = await registry.list_tools()
    assert len(tools) >= 2


@pytest.mark.asyncio
async def test_execute_tool(registry):
    """Test tool execution."""
    async def echo_executor(params, context):
        return {"echo": params.get("message", "")}

    await registry.register_tool(
        name="echo",
        executor=echo_executor
    )

    result = await registry.execute(
        tool_name="echo",
        parameters={"message": "Hello"}
    )

    assert result["success"] is True
    assert result["result"]["echo"] == "Hello"


@pytest.mark.asyncio
async def test_builtin_tools(registry):
    """Test registering built-in tools."""
    await registry.register_builtin_tools()

    tools = await registry.list_tools()
    tool_names = [t.name for t in tools]

    assert "http_request" in tool_names
    assert "web_search" in tool_names
    assert "database" in tool_names
    assert "execute_code" in tool_names


@pytest.mark.asyncio
async def test_disable_tool(registry):
    """Test disabling a tool."""
    async def dummy_executor(params, context):
        return {}

    await registry.register_tool(name="test_tool", executor=dummy_executor)
    await registry.disable_tool("test_tool")

    tool = await registry.get_tool("test_tool")
    assert tool.enabled is False


# Day 8: Web Search Tool Tests

@pytest.mark.asyncio
async def test_web_search_tool_exists(registry):
    """Test that web_search tool is registered."""
    await registry.register_builtin_tools()

    tool = await registry.get_tool("web_search")
    assert tool is not None
    assert tool.name == "web_search"


@pytest.mark.asyncio
async def test_web_search_api_tool_exists(registry):
    """Test that web_search_api tool is registered."""
    await registry.register_builtin_tools()

    tool = await registry.get_tool("web_search_api")
    assert tool is not None
    assert tool.name == "web_search_api"


def test_web_search_direct():
    """Test web search tool directly."""
    from core.tools.web_search import WebSearchTool

    tool = WebSearchTool()
    # Just test the tool initialization - don't actually search
    assert tool is not None
    assert tool.search_engine == "ddg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
