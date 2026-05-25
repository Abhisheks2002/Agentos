"""Tests for AgentOS Memory."""

import pytest
import asyncio
from core.memory.memory import MemoryManager, VectorStore


@pytest.fixture
def memory_manager():
    """Create a memory manager instance."""
    return MemoryManager()


@pytest.mark.asyncio
async def test_add_short_term_memory(memory_manager):
    """Test adding short-term memory."""
    memory_id = await memory_manager.add_short_term(
        agent_id="agent_1",
        content="This is a test memory",
        metadata={"source": "test"}
    )

    assert memory_id is not None
    assert memory_id.startswith("mem_")


@pytest.mark.asyncio
async def test_get_short_term_memory(memory_manager):
    """Test getting short-term memory."""
    await memory_manager.add_short_term(
        agent_id="agent_1",
        content="Memory 1"
    )
    await memory_manager.add_short_term(
        agent_id="agent_1",
        content="Memory 2"
    )

    memories = await memory_manager.get_short_term("agent_1")
    assert len(memories) >= 2


@pytest.mark.asyncio
async def test_add_long_term_memory(memory_manager):
    """Test adding long-term memory."""
    memory_id = await memory_manager.add_long_term(
        agent_id="agent_1",
        content="Important information",
        metadata={"importance": "high"}
    )

    assert memory_id is not None


@pytest.mark.asyncio
async def test_search_memory(memory_manager):
    """Test semantic search."""
    await memory_manager.add_short_term(
        agent_id="agent_1",
        content="The quick brown fox"
    )
    await memory_manager.add_short_term(
        agent_id="agent_1",
        content="Python programming language"
    )

    results = await memory_manager.search(
        agent_id="agent_1",
        query="programming",
        limit=5
    )

    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_working_memory(memory_manager):
    """Test working memory."""
    await memory_manager.set_working("agent_1", "counter", 0)
    value = await memory_manager.get_working("agent_1", "counter")

    assert value == 0


@pytest.mark.asyncio
async def test_clear_short_term_memory(memory_manager):
    """Test clearing short-term memory."""
    await memory_manager.add_short_term(
        agent_id="agent_1",
        content="Temporary memory"
    )

    await memory_manager.clear_short_term("agent_1")
    memories = await memory_manager.get_short_term("agent_1")

    assert len(memories) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
