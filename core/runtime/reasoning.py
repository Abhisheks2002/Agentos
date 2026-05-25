"""Chain-of-Thought Reasoning Engine for AgentOS - Day 7 Implementation.

Provides step-by-step reasoning capabilities including:
- Reasoning traces
- Thought chains with branching
- Reflection and self-evaluation
- Multi-step planning with replanning
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning strategies."""
    CHAIN = "chain"  # Linear chain of thought
    TREE = "tree"    # Branching thought exploration
    REFLEXION = "reflexion"  # Self-reflection based
    REACT = "react"  # Reason + Act pattern


class ThoughtStatus(str, Enum):
    """Status of a thought in the reasoning chain."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    REVISED = "revised"


@dataclass
class Thought:
    """A single thought in the reasoning chain."""
    id: str = field(default_factory=lambda: f"thought_{uuid.uuid4().hex[:12]}")
    content: str = ""
    reasoning_type: ReasoningType = ReasoningType.CHAIN
    status: ThoughtStatus = ThoughtStatus.PENDING
    confidence: float = 0.0  # 0.0 to 1.0
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    tool_used: Optional[str] = None
    tool_result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "reasoning_type": self.reasoning_type.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "tool_used": self.tool_used,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms
        }


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for an agent task."""
    id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    agent_id: str = ""
    task_id: str = ""
    reasoning_type: ReasoningType = ReasoningType.CHAIN
    thoughts: List[Thought] = field(default_factory=list)
    current_thought_id: Optional[str] = None
    final_answer: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_thought(self, thought: Thought) -> None:
        """Add a thought to the trace."""
        self.thoughts.append(thought)
        self.current_thought_id = thought.id

        # Update parent's children
        if thought.parent_id:
            for t in self.thoughts:
                if t.id == thought.parent_id:
                    t.child_ids.append(thought.id)
                    break

    def get_current_thought(self) -> Optional[Thought]:
        """Get the current active thought."""
        if self.current_thought_id:
            for t in self.thoughts:
                if t.id == self.current_thought_id:
                    return t
        return None

    def get_thought_chain(self) -> List[Thought]:
        """Get the linear chain of thoughts (for CHAIN reasoning)."""
        if not self.thoughts:
            return []

        # Find the first thought (no parent)
        first = None
        for t in self.thoughts:
            if t.parent_id is None:
                first = t
                break

        if not first:
            return self.thoughts

        # Follow the chain
        chain = [first]
        current = first
        while current.child_ids:
            next_id = current.child_ids[0]
            next_thought = next((t for t in self.thoughts if t.id == next_id), None)
            if next_thought:
                chain.append(next_thought)
                current = next_thought
            else:
                break

        return chain

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "reasoning_type": self.reasoning_type.value,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "current_thought_id": self.current_thought_id,
            "final_answer": self.final_answer,
            "success": self.success,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
            "metadata": self.metadata
        }


class ReasoningEngine:
    """
    Chain-of-Thought reasoning engine for agents.

    Supports multiple reasoning strategies:
    - Chain: Linear step-by-step reasoning
    - Tree: Branching exploration of multiple paths
    - Reflexion: Self-reflection and correction
    - ReAct:交替 reasoning and action execution
    """

    def __init__(self, max_thoughts: int = 50, max_depth: int = 10):
        self.max_thoughts = max_thoughts
        self.max_depth = max_depth
        self.active_traces: Dict[str, ReasoningTrace] = {}
        self._tool_executor: Optional[Callable] = None

    def set_tool_executor(self, executor: Callable) -> None:
        """Set the tool executor function."""
        self._tool_executor = executor

    def create_trace(
        self,
        agent_id: str,
        task_id: str,
        reasoning_type: ReasoningType = ReasoningType.CHAIN,
        metadata: Dict[str, Any] = None
    ) -> ReasoningTrace:
        """Create a new reasoning trace."""
        trace = ReasoningTrace(
            agent_id=agent_id,
            task_id=task_id,
            reasoning_type=reasoning_type,
            metadata=metadata or {}
        )
        self.active_traces[trace.id] = trace
        logger.info(f"Created reasoning trace {trace.id} for agent {agent_id}")
        return trace

    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Get a reasoning trace by ID."""
        return self.active_traces.get(trace_id)

    async def add_reasoning_step(
        self,
        trace_id: str,
        content: str,
        parent_id: Optional[str] = None,
        reasoning_type: ReasoningType = ReasoningType.CHAIN,
        metadata: Dict[str, Any] = None
    ) -> Optional[Thought]:
        """Add a reasoning step to the trace."""
        trace = self.active_traces.get(trace_id)
        if not trace:
            logger.error(f"Trace {trace_id} not found")
            return None

        # Check max thoughts limit
        if len(trace.thoughts) >= self.max_thoughts:
            logger.warning(f"Max thoughts reached for trace {trace_id}")
            return None

        thought = Thought(
            content=content,
            reasoning_type=reasoning_type,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        trace.add_thought(thought)
        logger.debug(f"Added thought {thought.id} to trace {trace_id}")
        return thought

    async def execute_with_reasoning(
        self,
        agent_id: str,
        task_id: str,
        task_input: str,
        reason_func: Callable,
        reasoning_type: ReasoningType = ReasoningType.CHAIN,
        max_iterations: int = 10
    ) -> ReasoningTrace:
        """
        Execute a task with reasoning.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            task_input: The task input/prompt
            reason_func: Async function that takes (trace, current_thought) and returns next step
            reasoning_type: Type of reasoning to use
            max_iterations: Maximum reasoning iterations

        Returns:
            ReasoningTrace with the complete reasoning process
        """
        trace = self.create_trace(agent_id, task_id, reasoning_type)

        # Initial thought
        initial_thought = await self.add_reasoning_step(
            trace_id=trace.id,
            content=f"Task: {task_input}",
            reasoning_type=reasoning_type
        )

        if not initial_thought:
            trace.error = "Failed to create initial thought"
            return trace

        # Iterative reasoning
        for iteration in range(max_iterations):
            current = trace.get_current_thought()
            if not current:
                break

            current.status = ThoughtStatus.IN_PROGRESS
            start_time = datetime.now()

            try:
                # Execute reasoning step
                result = await reason_func(trace, current)

                if result is None:
                    # No more steps, reasoning complete
                    break

                end_time = datetime.now()
                current.duration_ms = int((end_time - start_time).total_seconds() * 1000)
                current.status = ThoughtStatus.COMPLETED
                current.completed_at = end_time

                # Check if result contains final answer
                if isinstance(result, dict):
                    if result.get("final_answer"):
                        trace.final_answer = result["final_answer"]
                        trace.success = True
                        break
                    if result.get("thought"):
                        # Add next thought
                        await self.add_reasoning_step(
                            trace_id=trace.id,
                            content=result["thought"],
                            parent_id=current.id,
                            reasoning_type=reasoning_type,
                            metadata=result.get("metadata", {})
                        )
                elif isinstance(result, str):
                    # Result is the next thought content
                    await self.add_reasoning_step(
                        trace_id=trace.id,
                        content=result,
                        parent_id=current.id,
                        reasoning_type=reasoning_type
                    )

            except Exception as e:
                logger.exception(f"Reasoning step failed: {e}")
                current.status = ThoughtStatus.REJECTED
                current.metadata["error"] = str(e)
                trace.error = str(e)
                break

        # Finalize trace
        trace.completed_at = datetime.now()
        if trace.created_at:
            trace.total_duration_ms = int(
                (trace.completed_at - trace.created_at).total_seconds() * 1000
            )

        logger.info(f"Completed reasoning trace {trace.id}, success: {trace.success}")
        return trace

    async def reflect(
        self,
        trace_id: str,
        reflection_prompt: str = "Review your reasoning and identify any issues."
    ) -> Optional[Thought]:
        """
        Perform self-reflection on the reasoning trace.

        Used in Reflexion strategy to review and correct reasoning.
        """
        trace = self.active_traces.get(trace_id)
        if not trace:
            return None

        # Get the chain so far
        chain = trace.get_thought_chain()

        # Create reflection thought
        reflection = Thought(
            content=f"Reflection: {reflection_prompt}\n\nPrevious reasoning:\n" +
                    "\n".join([f"- {t.content}" for t in chain[-3:]]),
            reasoning_type=ReasoningType.REFLEXION,
            parent_id=trace.current_thought_id,
            metadata={"type": "reflection", "chain_length": len(chain)}
        )

        trace.add_thought(reflection)
        return reflection

    async def execute_tool(
        self,
        trace_id: str,
        tool_name: str,
        tool_params: Dict[str, Any]
    ) -> Any:
        """Execute a tool within the reasoning context."""
        trace = self.active_traces.get(trace_id)
        current = trace.get_current_thought() if trace else None

        if not self._tool_executor:
            logger.warning("No tool executor configured")
            return None

        try:
            result = await self._tool_executor(tool_name, tool_params)

            # Record tool use in current thought
            if current:
                current.tool_used = tool_name
                current.tool_result = result

            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            if current:
                current.metadata["tool_error"] = str(e)
            return None

    def clear_trace(self, trace_id: str) -> bool:
        """Clear a reasoning trace from memory."""
        if trace_id in self.active_traces:
            del self.active_traces[trace_id]
            return True
        return False

    def get_trace_summary(self, trace_id: str) -> Optional[dict]:
        """Get a summary of a reasoning trace."""
        trace = self.active_traces.get(trace_id)
        if not trace:
            return None

        return {
            "id": trace.id,
            "agent_id": trace.agent_id,
            "task_id": trace.task_id,
            "reasoning_type": trace.reasoning_type.value,
            "thought_count": len(trace.thoughts),
            "success": trace.success,
            "final_answer": trace.final_answer[:200] if trace.final_answer else None,
            "total_duration_ms": trace.total_duration_ms
        }


# Global reasoning engine instance
_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get the global reasoning engine instance."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine