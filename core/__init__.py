"""AgentOS - AI Operating System for Autonomous Agents

A comprehensive platform for managing AI agents, tools, memory, and workflows.
"""

__version__ = "0.1.0"
__author__ = "AgentOS Team"

from .runtime.runtime import AgentRuntime, get_runtime
from .memory.memory import MemoryManager, get_memory_manager
from .tools.registry import ToolRegistry, get_tool_registry
from .governance.governance import GovernanceEngine, get_governance_engine
from .models.models import Agent, AgentType, AgentStatus, Task, Tool, Memory, Workflow

# Day 8: AI Agent Development
from .agent import Agent as AIAgent, AgentResponse, Perception, Action, AgentArchitecture
from .agent_builder import AgentBuilder, BookingAgentBuilder, create_booking_agent
from .multi_agent import AgentTeam, CollaborationPattern, create_team

__all__ = [
    # Runtime
    "AgentRuntime",
    "get_runtime",
    # Memory
    "MemoryManager",
    "get_memory_manager",
    # Tools
    "ToolRegistry",
    "get_tool_registry",
    # Governance
    "GovernanceEngine",
    "get_governance_engine",
    # Models
    "Agent",
    "AgentType",
    "AgentStatus",
    "Task",
    "Tool",
    "Memory",
    "Workflow",
    # Day 8: AI Agent Development
    "AIAgent",
    "AgentResponse",
    "Perception",
    "Action",
    "AgentArchitecture",
    "AgentBuilder",
    "BookingAgentBuilder",
    "create_booking_agent",
    "AgentTeam",
    "CollaborationPattern",
    "create_team",
]