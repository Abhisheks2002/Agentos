"""AgentOS - AI Agent Core Implementation (Day 8)

This module provides the core Agent class that integrates:
- Perception (input processing)
- Reasoning (LLM-powered thought process)
- Memory (short-term and long-term)
- Tool Use (actions and APIs)
- Learning (from interactions)

The agent follows the architecture: Perception → Reasoning → Action
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
import logging

from .models.models import Agent, AgentStatus, AgentType, Task
from .reasoning.chain_of_thought import (
    ChainOfThought, ReasoningType, ReasoningResult, get_reasoning_engine
)
from .memory.memory import MemoryManager, get_memory_manager
from .tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)


class AgentArchitecture(Enum):
    """Types of agent architectures."""
    SIMPLE_REFLEX = "simple_reflex"  # Rule-based responses
    MODEL_REFLEX = "model_reflex"    # Uses internal model
    GOAL_BASED = "goal_based"        # Plans to achieve goals
    UTILITY_BASED = "utility_based"  # Maximizes utility function
    LEARNING = "learning"            # Learns from feedback


@dataclass
class Perception:
    """Perception layer - processes inputs from environment."""
    raw_input: Any
    input_type: str  # text, image, audio, tool_result, event
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def extract_text(self) -> str:
        """Extract text from perception."""
        if isinstance(self.raw_input, str):
            return self.raw_input
        elif isinstance(self.raw_input, dict):
            return self.raw_input.get("text", str(self.raw_input))
        return str(self.raw_input)


@dataclass
class Action:
    """Action layer - executes tools and returns responses."""
    action_type: str  # tool_call, response, plan, pause
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    plan: Optional[List[Dict]] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "response": self.response,
            "plan": self.plan,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentResponse:
    """Complete response from agent execution."""
    success: bool
    output: Any
    actions: List[Action] = field(default_factory=list)
    reasoning: Optional[ReasoningResult] = None
    memory_updates: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


class Agent:
    """
    Core AI Agent class implementing the Perception → Reasoning → Action architecture.

    Features:
    - Multiple reasoning strategies (CoT, ToT, ReAct, Reflexion)
    - Memory systems (short-term, long-term, working)
    - Tool execution with governance
    - Learning from interactions
    - Multiple agent architectures
    """

    def __init__(
        self,
        name: str,
        agent_type: AgentType = AgentType.CHAT,
        architecture: AgentArchitecture = AgentArchitecture.GOAL_BASED,
        system_prompt: str = None,
        tools: List[str] = None,
        memory_manager: MemoryManager = None,
        tool_registry: ToolRegistry = None,
        reasoning_engine: ChainOfThought = None,
        config: Dict[str, Any] = None
    ):
        """Initialize the agent.

        Args:
            name: Agent name
            agent_type: Type of agent (CHAT, WORKFLOW, AUTONOMOUS, ORCHESTRATOR)
            architecture: Agent architecture type
            system_prompt: System prompt defining agent behavior
            tools: List of tool names available to this agent
            memory_manager: Memory manager instance
            tool_registry: Tool registry instance
            reasoning_engine: Reasoning engine instance
            config: Additional configuration
        """
        self.id = f"agent_{uuid.uuid4().hex[:12]}"
        self.name = name
        self.agent_type = agent_type
        self.architecture = architecture
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.tools = tools or []
        self.config = config or {}

        # Runtime components
        self.memory_manager = memory_manager or get_memory_manager()
        self.tool_registry = tool_registry or get_tool_registry()
        self.reasoning_engine = reasoning_engine or get_reasoning_engine()

        # State
        self.status = AgentStatus.CREATED
        self.session_id = None
        self.current_task = None

        # History
        self.interaction_history: List[Dict] = []
        self.tools_used: Dict[str, int] = {}

        # Callbacks
        self._pre_perception: Optional[Callable] = None
        self._post_action: Optional[Callable] = None

        logger.info(f"Created agent: {self.id} - {self.name}")

    def _default_system_prompt(self) -> str:
        """Default system prompt."""
        return f"""You are {self.name}, an AI agent.
You have access to tools to help you accomplish tasks.
Think step by step and use tools when needed.
Always explain your reasoning."""

    # ==================== Lifecycle ====================

    async def start(self) -> bool:
        """Start the agent and initialize resources."""
        if self.status != AgentStatus.CREATED:
            return False

        self.status = AgentStatus.RUNNING

        # Start memory session
        if self.memory_manager:
            self.session_id = self.memory_manager.start_session(self.id, {
                "agent_name": self.name,
                "agent_type": self.agent_type.value,
                "architecture": self.architecture.value
            })

        logger.info(f"Agent started: {self.id}")
        return True

    async def stop(self):
        """Stop the agent and cleanup resources."""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.COMPLETED

        # End memory session
        if self.memory_manager and self.session_id:
            self.memory_manager.end_session(self.id)

        logger.info(f"Agent stopped: {self.id}")

    async def pause(self):
        """Pause the agent."""
        self.status = AgentStatus.PAUSED
        logger.info(f"Agent paused: {self.id}")

    async def resume(self):
        """Resume the agent."""
        self.status = AgentStatus.RUNNING
        logger.info(f"Agent resumed: {self.id}")

    # ==================== Core Execution ====================

    async def run(
        self,
        input_data: Union[str, Dict, Perception],
        context: Dict[str, Any] = None,
        use_reasoning: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT
    ) -> AgentResponse:
        """
        Main agent execution loop: Perception → Reasoning → Action

        Args:
            input_data: Raw input (text, dict, or Perception object)
            context: Additional context for this execution
            use_reasoning: Reasoning strategy to use

        Returns:
            AgentResponse with output and metadata
        """
        start_time = datetime.now()
        context = context or {}

        try:
            # Step 1: Perception - process input
            perception = await self._perceive(input_data, context)

            # Step 2: Reasoning - think about what to do
            reasoning_result = await self._reason(
                perception, context, use_reasoning
            )

            # Step 3: Action - execute tools and generate response
            actions = await self._act(perception, reasoning_result, context)

            # Step 4: Learn - update memory with interaction
            await self._learn(perception, reasoning_result, actions)

            # Execute post-action callbacks
            if self._post_action:
                await self._post_action(perception, actions)

            execution_time = (datetime.now() - start_time).total_seconds()

            return AgentResponse(
                success=True,
                output=actions[-1].response if actions else "No action taken",
                actions=actions,
                reasoning=reasoning_result,
                execution_time=execution_time,
                metadata={
                    "agent_id": self.id,
                    "agent_name": self.name,
                    "perception_type": perception.input_type
                }
            )

        except Exception as e:
            logger.exception(f"Agent execution failed: {self.id}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResponse(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"agent_id": self.id}
            )

    async def _perceive(
        self,
        input_data: Union[str, Dict, Perception],
        context: Dict[str, Any]
    ) -> Perception:
        """Perception layer - process input."""
        # Run pre-perception callback
        if self._pre_perception:
            input_data = self._pre_perception(input_data) or input_data

        # Convert to Perception object
        if isinstance(input_data, Perception):
            perception = input_data
        elif isinstance(input_data, str):
            perception = Perception(
                raw_input=input_data,
                input_type="text",
                context=context
            )
        elif isinstance(input_data, dict):
            perception = Perception(
                raw_input=input_data,
                input_type=input_data.get("type", "data"),
                context=context
            )
        else:
            perception = Perception(
                raw_input=str(input_data),
                input_type="unknown",
                context=context
            )

        # Add session context to perception
        if self.session_id:
            perception.context["session_id"] = self.session_id

        logger.debug(f"Perception: {perception.input_type} - {perception.extract_text()[:50]}...")
        return perception

    async def _reason(
        self,
        perception: Perception,
        context: Dict[str, Any],
        reasoning_type: ReasoningType
    ) -> ReasoningResult:
        """Reasoning layer - think about the input."""
        # Build context for reasoning
        reasoning_context = {
            "system_prompt": self.system_prompt,
            "agent_name": self.name,
            "available_tools": self.tools,
            "history": self.interaction_history[-5:],  # Last 5 interactions
            **context
        }

        # Get relevant memories
        if self.memory_manager:
            relevant_memories = self.memory_manager.recall_knowledge(
                perception.extract_text()
            )
            reasoning_context["relevant_memories"] = relevant_memories

        # Prepare tools for ReAct reasoning
        tools = []
        for tool_name in self.tools:
            tool = self.tool_registry.get(tool_name)
            if tool:
                tools.append(tool.to_dict())

        # Execute reasoning
        result = await self.reasoning_engine.reason(
            problem=perception.extract_text(),
            reasoning_type=reasoning_type,
            context=reasoning_context,
            tools=tools if reasoning_type == ReasoningType.REACT else None
        )

        logger.debug(f"Reasoning: {result.reasoning_type.value} - {result.final_answer[:50] if result.final_answer else 'No conclusion'}...")
        return result

    async def _act(
        self,
        perception: Perception,
        reasoning_result: ReasoningResult,
        context: Dict[str, Any]
    ) -> List[Action]:
        """Action layer - execute tools and generate response."""
        actions = []

        # Determine action based on reasoning
        if reasoning_result.final_answer:
            # Use the reasoning result as the response
            action = Action(
                action_type="response",
                response=reasoning_result.final_answer,
                confidence=reasoning_result.confidence
            )
            actions.append(action)

        # Check if tools should be called based on reasoning
        if reasoning_result.steps:
            for step in reasoning_result.steps:
                if step.action and step.action != "None":
                    # Execute the tool
                    tool_result = await self._execute_tool(step.action, {})
                    action = Action(
                        action_type="tool_call",
                        tool_name=step.action,
                        tool_params={},
                        response=str(tool_result),
                        confidence=step.confidence
                    )
                    actions.append(action)

        # If no actions generated, create a default response
        if not actions:
            response_text = f"I understand: {perception.extract_text()}"
            if reasoning_result.final_answer:
                response_text = reasoning_result.final_answer

            action = Action(
                action_type="response",
                response=response_text,
                confidence=0.8
            )
            actions.append(action)

        return actions

    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        # Check if tool exists
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {"error": f"Tool {tool_name} not registered"}

        # Track tool usage
        self.tools_used[tool_name] = self.tools_used.get(tool_name, 0) + 1

        # Execute tool via registry
        try:
            result = await self.tool_registry.execute_tool(tool_name, params)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {"error": str(e)}

    async def _learn(
        self,
        perception: Perception,
        reasoning_result: ReasoningResult,
        actions: List[Action]
    ):
        """Learning layer - update memory with interaction."""
        if not self.memory_manager:
            return

        # Store interaction in episodic memory
        self.memory_manager.add_interaction(
            self.id,
            "agent_interaction",
            f"Input: {perception.extract_text()[:100]}",
            {
                "perception_type": perception.input_type,
                "reasoning_type": reasoning_result.reasoning_type.value,
                "actions_count": len(actions),
                "confidence": reasoning_result.confidence
            }
        )

        # Store important facts in semantic memory
        if reasoning_result.final_answer:
            self.memory_manager.store_knowledge(
                f"Agent {self.name} processed: {perception.extract_text()[:50]}",
                [self.name, "interaction"]
            )

    # ==================== Tool Use ====================

    async def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """Directly call a tool by name."""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool {tool_name} not available"}

        return await self._execute_tool(tool_name, kwargs)

    def add_tool(self, tool_name: str):
        """Add a tool to the agent."""
        if tool_name not in self.tools:
            self.tools.append(tool_name)
            logger.info(f"Added tool {tool_name} to agent {self.id}")

    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent."""
        if tool_name in self.tools:
            self.tools.remove(tool_name)
            logger.info(f"Removed tool {tool_name} from agent {self.id}")

    # ==================== Planning ====================

    async def plan(self, goal: str, max_steps: int = 5) -> List[Dict]:
        """Create a plan to achieve a goal."""
        plan = []

        # Use reasoning to break down the goal
        reasoning_result = await self.reasoning_engine.reason(
            problem=f"Create a plan to achieve: {goal}",
            reasoning_type=ReasoningType.TREE_OF_THOUGHTS,
            context={
                "available_tools": self.tools,
                "max_steps": max_steps
            }
        )

        # Extract plan from reasoning
        if reasoning_result.steps:
            for i, step in enumerate(reasoning_result.steps[:max_steps]):
                plan.append({
                    "step": i + 1,
                    "thought": step.thought,
                    "action": step.action,
                    "status": "pending"
                })

        logger.info(f"Created plan with {len(plan)} steps for goal: {goal}")
        return plan

    async def execute_plan(self, plan: List[Dict]) -> List[Dict]:
        """Execute a previously created plan."""
        results = []

        for step in plan:
            if step.get("status") == "completed":
                continue

            # Execute step
            if step.get("action"):
                tool_result = await self._execute_tool(step["action"], {})
                step["result"] = tool_result
                step["status"] = "completed"
            else:
                step["status"] = "skipped"

            results.append(step)

        return results

    # ==================== Reflection ====================

    async def reflect(self) -> Dict:
        """Reflect on recent interactions and improve."""
        if not self.interaction_history:
            return {"reflection": "No interactions to reflect on"}

        # Get recent interactions
        recent = self.interaction_history[-10:]

        # Analyze patterns
        total_interactions = len(self.interaction_history)
        successful = sum(1 for i in recent if i.get("success", False))
        tools_most_used = max(self.tools_used.items(), key=lambda x: x[1]) if self.tools_used else (None, 0)

        reflection = {
            "total_interactions": total_interactions,
            "recent_success_rate": successful / len(recent) if recent else 0,
            "most_used_tool": tools_most_used[0],
            "tools_used_count": dict(self.tools_used),
            "recommendations": []
        }

        # Generate recommendations
        if successful / len(recent) < 0.7 if recent else False:
            reflection["recommendations"].append(
                "Consider adjusting the system prompt for better responses"
            )

        if not self.tools_used:
            reflection["recommendations"].append(
                "Try using more tools to accomplish tasks"
            )

        logger.info(f"Agent {self.id} reflected: {reflection['recent_success_rate']:.0%} success rate")
        return reflection

    # ==================== Serialization ====================

    def to_dict(self) -> Dict:
        """Serialize agent to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type.value,
            "architecture": self.architecture.value,
            "status": self.status.value,
            "tools": self.tools,
            "system_prompt": self.system_prompt,
            "session_id": self.session_id,
            "tools_used": self.tools_used,
            "interaction_count": len(self.interaction_history),
            "config": self.config
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Agent':
        """Deserialize agent from dictionary."""
        agent = cls(
            name=data["name"],
            agent_type=AgentType(data.get("type", "chat")),
            architecture=AgentArchitecture(data.get("architecture", "goal_based")),
            system_prompt=data.get("system_prompt"),
            tools=data.get("tools", []),
            config=data.get("config", {})
        )
        agent.id = data.get("id", agent.id)
        agent.status = AgentStatus(data.get("status", "created"))
        return agent


# Global agent registry
_agents: Dict[str, Agent] = {}


def get_agent(agent_id: str) -> Optional[Agent]:
    """Get an agent by ID."""
    return _agents.get(agent_id)


def register_agent(agent: Agent):
    """Register an agent."""
    _agents[agent.id] = agent


def unregister_agent(agent_id: str):
    """Unregister an agent."""
    if agent_id in _agents:
        del _agents[agent_id]


def list_agents() -> List[Dict]:
    """List all registered agents."""
    return [agent.to_dict() for agent in _agents.values()]