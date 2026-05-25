"""Agent Builder - Practical agent creation (Day 8)

Provides a builder pattern for creating agents with:
- Custom tools (function definitions)
- System prompts
- Memory configuration
- Reasoning strategies
"""

import uuid
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .agent import Agent, AgentArchitecture, AgentResponse, Perception
from .models.models import AgentType
from .reasoning.chain_of_thought import ReasoningType
from .tools.registry import ToolRegistry, get_tool_registry


@dataclass
class ToolDefinition:
    """Tool definition for agent builder."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None


class AgentBuilder:
    """
    Builder for creating agents with custom configuration.

    Example usage:
        agent = (AgentBuilder("Booking Agent")
            .with_tools([
                {"name": "get_available_slots", ...},
                {"name": "book_slot", ...}
            ])
            .with_system_prompt("You are a booking assistant...")
            .with_reasoning(ReasoningType.REACT)
            .build())
    """

    def __init__(self, name: str):
        """Initialize the builder."""
        self._name = name
        self._agent_type = AgentType.CHAT
        self._architecture = AgentArchitecture.GOAL_BASED
        self._system_prompt = None
        self._tools: List[str] = []
        self._tool_definitions: List[ToolDefinition] = []
        self._reasoning_type = ReasoningType.CHAIN_OF_THOUGHT
        self._memory_enabled = True
        self._config: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}

    def with_type(self, agent_type: AgentType) -> 'AgentBuilder':
        """Set agent type."""
        self._agent_type = agent_type
        return self

    def with_architecture(self, architecture: AgentArchitecture) -> 'AgentBuilder':
        """Set agent architecture."""
        self._architecture = architecture
        return self

    def with_system_prompt(self, prompt: str) -> 'AgentBuilder':
        """Set system prompt."""
        self._system_prompt = prompt
        return self

    def with_tools(self, tools: List[Union[str, Dict]]) -> 'AgentBuilder':
        """Add tools to the agent.

        Args:
            tools: List of tool names or tool definitions
        """
        for tool in tools:
            if isinstance(tool, str):
                self._tools.append(tool)
            elif isinstance(tool, dict):
                tool_name = tool.get("name")
                if tool_name:
                    self._tools.append(tool_name)

                    # Register tool if not already registered
                    self._tool_definitions.append(ToolDefinition(
                        name=tool_name,
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {}),
                        handler=tool.get("handler")
                    ))
        return self

    def with_tool(self, name: str, description: str, parameters: Dict,
                  handler: Callable = None) -> 'AgentBuilder':
        """Add a single tool."""
        self._tools.append(name)
        self._tool_definitions.append(ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        ))
        return self

    def with_reasoning(self, reasoning_type: ReasoningType) -> 'AgentBuilder':
        """Set default reasoning type."""
        self._reasoning_type = reasoning_type
        return self

    def with_memory(self, enabled: bool = True) -> 'AgentBuilder':
        """Enable/disable memory."""
        self._memory_enabled = enabled
        return self

    def with_config(self, **kwargs) -> 'AgentBuilder':
        """Add configuration options."""
        self._config.update(kwargs)
        return self

    def with_callback(self, event: str, callback: Callable) -> 'AgentBuilder':
        """Add a callback for events."""
        self._callbacks[event] = callback
        return self

    def build(self) -> Agent:
        """Build the agent."""
        # Register tools with the registry
        tool_registry = get_tool_registry()
        for tool_def in self._tool_definitions:
            if not tool_registry.get(tool_def.name):
                tool_registry.register(
                    name=tool_def.name,
                    description=tool_def.description,
                    parameters=tool_def.parameters,
                    handler=tool_def.handler
                )

        # Build system prompt if not provided
        system_prompt = self._system_prompt or self._default_prompt()

        # Create the agent
        agent = Agent(
            name=self._name,
            agent_type=self._agent_type,
            architecture=self._architecture,
            system_prompt=system_prompt,
            tools=self._tools,
            config=self._config
        )

        # Set callbacks
        if "pre_perception" in self._callbacks:
            agent._pre_perception = self._callbacks["pre_perception"]
        if "post_action" in self._callbacks:
            agent._post_action = self._callbacks["post_action"]

        return agent

    def _default_prompt(self) -> str:
        """Generate default prompt based on tools."""
        tool_descriptions = []
        for tool in self._tools:
            tool_descriptions.append(f"- {tool}")

        return f"""You are {self.name}, an AI assistant.

You have access to the following tools:
{chr(10).join(tool_descriptions)}

Instructions:
- Use tools to accomplish tasks when appropriate
- Think step by step
- Provide clear and helpful responses"""


class BookingAgentBuilder(AgentBuilder):
    """Specialized builder for booking agents (from Day 8 PDF example)."""

    def __init__(self):
        super().__init__("Booking Agent")
        self._with_booking_tools()

    def _with_booking_tools(self):
        """Add booking-specific tools."""
        self.with_tool(
            name="get_available_slots",
            description="Get available appointment slots",
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "service": {"type": "string", "description": "Service type"}
                },
                "required": ["date"]
            }
        ).with_tool(
            name="book_slot",
            description="Book an appointment slot",
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time": {"type": "string", "description": "Time slot"},
                    "service": {"type": "string", "description": "Service type"},
                    "customer_name": {"type": "string", "description": "Customer name"},
                    "customer_email": {"type": "string", "description": "Customer email"}
                },
                "required": ["date", "time", "service", "customer_name"]
            }
        ).with_tool(
            name="cancel_booking",
            description="Cancel an existing booking",
            parameters={
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Booking ID to cancel"}
                },
                "required": ["booking_id"]
            }
        ).with_tool(
            name="get_booking_status",
            description="Check booking status",
            parameters={
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Booking ID"}
                },
                "required": ["booking_id"]
            }
        ).with_system_prompt("""You are a booking assistant for a service business.

Your capabilities:
- Check available appointment slots
- Book appointments for customers
- Cancel bookings
- Check booking status

When booking:
1. First check available slots
2. Confirm the slot with the customer
3. Book the slot and provide confirmation

Always be friendly and helpful.""")


class DataAnalysisAgentBuilder(AgentBuilder):
    """Builder for data analysis agents."""

    def __init__(self):
        super().__init__("Data Analysis Agent")
        self._with_analysis_tools()

    def _with_analysis_tools(self):
        """Add data analysis tools."""
        self.with_tool(
            name="load_data",
            description="Load data from a file or database",
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Data source (file path or DB query)"},
                    "format": {"type": "string", "description": "Data format (csv, json, sql)"}
                },
                "required": ["source"]
            }
        ).with_tool(
            name="analyze_data",
            description="Analyze data with statistical methods",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Data to analyze"},
                    "method": {"type": "string", "description": "Analysis method (summary, correlation, regression)"}
                },
                "required": ["data", "method"]
            }
        ).with_tool(
            name="visualize_data",
            description="Create visualizations from data",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Data to visualize"},
                    "chart_type": {"type": "string", "description": "Chart type (bar, line, pie, scatter)"}
                },
                "required": ["data", "chart_type"]
            }
        ).with_tool(
            name="export_results",
            description="Export analysis results",
            parameters={
                "type": "object",
                "properties": {
                    "results": {"type": "object", "description": "Results to export"},
                    "format": {"type": "string", "description": "Export format (json, csv, pdf)"}
                },
                "required": ["results", "format"]
            }
        ).with_system_prompt("""You are a data analysis assistant.

Your capabilities:
- Load data from various sources
- Perform statistical analysis
- Create visualizations
- Export results in various formats

When analyzing:
1. First load and understand the data
2. Perform appropriate analysis
3. Present findings clearly
4. Create helpful visualizations""")


class ResearchAgentBuilder(AgentBuilder):
    """Builder for research agents."""

    def __init__(self):
        super().__init__("Research Agent")
        self._with_research_tools()

    def _with_research_tools(self):
        """Add research tools."""
        self.with_tool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                },
                "required": ["query"]
            }
        ).with_tool(
            name="read_content",
            description="Read content from a URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to read"}
                },
                "required": ["url"]
            }
        ).with_tool(
            name="summarize",
            description="Summarize text content",
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to summarize"},
                    "max_length": {"type": "integer", "description": "Max summary length", "default": 200}
                },
                "required": ["content"]
            }
        ).with_tool(
            name="save_notes",
            description="Save research notes",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic"},
                    "notes": {"type": "string", "description": "Notes to save"},
                    "tags": {"type": "array", "description": "Tags for organization"}
                },
                "required": ["topic", "notes"]
            }
        ).with_system_prompt("""You are a research assistant.

Your capabilities:
- Search the web for information
- Read and analyze web content
- Summarize long content
- Save organized research notes

When researching:
1. Search for relevant information
2. Read and analyze sources
3. Summarize key findings
4. Save organized notes""")


def create_booking_agent() -> Agent:
    """Create a pre-configured booking agent."""
    return BookingAgentBuilder().build()


def create_data_analysis_agent() -> Agent:
    """Create a pre-configured data analysis agent."""
    return DataAnalysisAgentBuilder().build()


def create_research_agent() -> Agent:
    """Create a pre-configured research agent."""
    return ResearchAgentBuilder().build()