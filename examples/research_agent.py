"""Research Agent - Example agent for web research

Demonstrates:
- Web search integration
- Content reading and summarization
- Knowledge storage
- Multi-step research workflows
"""

import asyncio
from typing import Any, Dict, List

from core.agent import Agent
from core.agent_builder import AgentBuilder
from core.models.models import AgentType
from core.reasoning.chain_of_thought import ReasoningType


def create_research_agent() -> Agent:
    """Create a research agent."""

    research_tools = [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10}
                },
                "required": ["query"]
            }
        },
        {
            "name": "read_content",
            "description": "Read content from a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to read"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "summarize",
            "description": "Summarize text content",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text to summarize"},
                    "max_length": {"type": "integer", "description": "Max words", "default": 200}
                },
                "required": ["content"]
            }
        },
        {
            "name": "save_notes",
            "description": "Save research notes",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic"},
                    "notes": {"type": "string", "description": "Notes content"},
                    "tags": {"type": "array", "description": "Topic tags"}
                },
                "required": ["topic", "notes"]
            }
        }
    ]

    agent = (
        AgentBuilder("Research Assistant")
        .with_type(AgentType.AUTONOMOUS)
        .with_tools(research_tools)
        .with_reasoning(ReasoningType.REACT)
        .with_system_prompt("""You are a research assistant.

Your workflow:
1. Search for relevant information using web_search
2. Read key sources using read_content
3. Summarize findings using summarize
4. Save organized notes using save_notes

Be thorough and cite your sources.""")
        .build()
    )

    return agent


class ResearchAgent:
    """Research Agent with integrated tools."""

    def __init__(self):
        self.agent = create_research_agent()
        self.notes: Dict[str, List[Dict]] = {}

        # Override tool execution with mock implementations
        async def execute_tool(tool_name: str, params: Dict):
            if tool_name == "web_search":
                return self._mock_web_search(params.get("query"), params.get("limit", 10))
            elif tool_name == "read_content":
                return self._mock_read_content(params.get("url"))
            elif tool_name == "summarize":
                return self._mock_summarize(params.get("content"), params.get("max_length", 200))
            elif tool_name == "save_notes":
                return self._save_notes(params.get("topic"), params.get("notes"), params.get("tags", []))
            return {"error": "Tool not found"}

        self.agent._execute_tool = execute_tool

    def _mock_web_search(self, query: str, limit: int) -> Dict:
        """Mock web search."""
        return {
            "success": True,
            "results": [
                {"title": f"Result {i+1} for {query}", "url": f"https://example.com/{i}", "snippet": f"Relevant information about {query}..."}
                for i in range(limit)
            ],
            "total": limit
        }

    def _mock_read_content(self, url: str) -> Dict:
        """Mock content reading."""
        return {
            "success": True,
            "url": url,
            "content": f"This is the content from {url}. It contains detailed information about the topic...",
            "word_count": 500
        }

    def _mock_summarize(self, content: str, max_length: int) -> Dict:
        """Mock summarization."""
        words = content.split()[:max_length]
        summary = " ".join(words)
        return {
            "success": True,
            "summary": summary,
            "original_length": len(content.split()),
            "summary_length": len(words)
        }

    def _save_notes(self, topic: str, notes: str, tags: List[str]) -> Dict:
        """Save research notes."""
        if topic not in self.notes:
            self.notes[topic] = []

        note_id = len(self.notes[topic]) + 1
        self.notes[topic].append({
            "id": note_id,
            "notes": notes,
            "tags": tags
        })

        return {
            "success": True,
            "note_id": note_id,
            "topic": topic,
            "message": f"Saved notes for topic: {topic}"
        }

    async def start(self):
        await self.agent.start()

    async def stop(self):
        await self.agent.stop()

    async def research(self, topic: str) -> Dict:
        """Conduct research on a topic."""
        response = await self.agent.run(f"Research {topic} and save important findings")
        return {
            "output": response.output,
            "notes": self.notes
        }

    def get_notes(self, topic: str = None) -> Dict:
        """Get saved notes."""
        if topic:
            return {"topic": topic, "notes": self.notes.get(topic, [])}
        return {"all_notes": self.notes}


async def run_research_demo():
    """Demo the research agent."""
    print("=" * 50)
    print("Research Agent Demo")
    print("=" * 50)

    agent = ResearchAgent()
    await agent.start()

    # Research a topic
    result = await agent.research("artificial intelligence")

    print(f"\nResearch output:\n{result['output']}")
    print(f"\nSaved notes: {agent.get_notes()}")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_research_demo())