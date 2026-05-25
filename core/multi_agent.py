"""Multi-Agent Collaboration System (Day 8)

Implements agent patterns from Day 8:
- Reflection: Agents review and improve their work
- Tool Use: Agents use tools effectively
- Planning: Agents create and execute plans
- Multi-Agent Collaboration: Multiple agents work together

Collaboration patterns:
- Sequential: Agents work one after another
- Parallel: Agents work simultaneously
- Hierarchical: Supervisor coordinates sub-agents
- Debate: Agents discuss and reach consensus
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging

from .agent import Agent, AgentResponse
from .models.models import AgentType

logger = logging.getLogger(__name__)


class CollaborationPattern(str, Enum):
    """Patterns for multi-agent collaboration."""
    SEQUENTIAL = "sequential"      # One after another
    PARALLEL = "parallel"           # Simultaneously
    HIERARCHICAL = "hierarchical"   # Supervisor + workers
    DEBATE = "debate"              # Discussion + consensus


@dataclass
class AgentMessage:
    """Message between agents."""
    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    sender_id: str = None
    sender_name: str = None
    receiver_id: str = None
    content: Any = None
    message_type: str = "message"  # message, request, response, tool_call
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class CollaborationTask:
    """Task for multi-agent collaboration."""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str = None
    pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL
    agents: List[str] = field(default_factory=list)  # Agent IDs
    status: str = "pending"  # pending, running, completed, failed
    results: List[Any] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class AgentTeam:
    """
    A team of agents working together.

    Supports multiple collaboration patterns:
    - Sequential: Pass output from one agent to the next
    - Parallel: All agents work on the same task simultaneously
    - Hierarchical: Supervisor delegates to workers and aggregates results
    - Debate: Agents discuss and vote on best answer
    """

    def __init__(
        self,
        name: str,
        pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL
    ):
        self.id = f"team_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.pattern = pattern
        self.agents: Dict[str, Agent] = {}
        self.supervisor: Optional[Agent] = None
        self.workers: List[Agent] = []
        self.message_history: List[AgentMessage] = []
        self._message_handlers: Dict[str, List[Callable]] = {}

        logger.info(f"Created agent team: {self.id} - {self.name}")

    def add_agent(self, agent: Agent, role: str = "worker") -> str:
        """Add an agent to the team."""
        self.agents[agent.id] = agent

        if role == "supervisor":
            self.supervisor = agent
        else:
            self.workers.append(agent)

        logger.info(f"Added agent {agent.id} to team {self.id} as {role}")
        return agent.id

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the team."""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        if agent == self.supervisor:
            self.supervisor = None
        else:
            self.workers = [a for a in self.workers if a.id != agent_id]

        del self.agents[agent_id]
        logger.info(f"Removed agent {agent_id} from team {self.id}")
        return True

    async def execute(
        self,
        task: str,
        context: Dict = None
    ) -> Dict:
        """Execute a task with the team."""
        context = context or {}

        if self.pattern == CollaborationPattern.SEQUENTIAL:
            return await self._execute_sequential(task, context)
        elif self.pattern == CollaborationPattern.PARALLEL:
            return await self._execute_parallel(task, context)
        elif self.pattern == CollaborationPattern.HIERARCHICAL:
            return await self._execute_hierarchical(task, context)
        elif self.pattern == CollaborationPattern.DEBATE:
            return await self._execute_debate(task, context)
        else:
            return await self._execute_sequential(task, context)

    async def _execute_sequential(
        self,
        task: str,
        context: Dict
    ) -> Dict:
        """Execute sequentially - each agent processes the output of the previous."""
        results = []
        current_input = task

        for agent in self.agents.values():
            # Start agent if needed
            if agent.status.value == "created":
                await agent.start()

            # Execute with previous output as context
            exec_context = {
                **context,
                "previous_results": results,
                "step": len(results) + 1,
                "total_steps": len(self.agents)
            }

            response = await agent.run(current_input, exec_context)
            results.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "output": response.output,
                "success": response.success
            })

            # Use output as next input
            current_input = response.output

        return {
            "team_id": self.id,
            "team_name": self.name,
            "pattern": self.pattern.value,
            "task": task,
            "results": results,
            "final_output": results[-1]["output"] if results else None,
            "success": all(r["success"] for r in results) if results else False
        }

    async def _execute_parallel(
        self,
        task: str,
        context: Dict
    ) -> Dict:
        """Execute in parallel - all agents work on the same task."""
        async def run_agent(agent: Agent):
            if agent.status.value == "created":
                await agent.start()

            exec_context = {**context, "task": task}
            return await agent.run(task, exec_context)

        # Run all agents in parallel
        tasks = [run_agent(agent) for agent in self.agents.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for agent, response in zip(self.agents.values(), responses):
            if isinstance(response, Exception):
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": None,
                    "success": False,
                    "error": str(response)
                })
            else:
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": response.output,
                    "success": response.success
                })

        # Aggregate results
        successful_results = [r for r in results if r["success"]]
        final_output = self._aggregate_results(successful_results)

        return {
            "team_id": self.id,
            "team_name": self.name,
            "pattern": self.pattern.value,
            "task": task,
            "results": results,
            "final_output": final_output,
            "success": len(successful_results) > 0
        }

    async def _execute_hierarchical(
        self,
        task: str,
        context: Dict
    ) -> Dict:
        """Execute hierarchically - supervisor delegates to workers."""
        if not self.supervisor:
            # Fall back to parallel if no supervisor
            return await self._execute_parallel(task, context)

        # Start supervisor
        if self.supervisor.status.value == "created":
            await self.supervisor.start()

        # Supervisor analyzes task and creates a plan
        plan_response = await self.supervisor.run(
            f"Break down this task and identify which workers should handle each part: {task}",
            {**context, "workers": [a.name for a in self.workers]}
        )

        # Assign work to workers (simulated - in real impl would parse the plan)
        worker_tasks = self._distribute_task(task, len(self.workers))

        # Run workers in parallel
        async def run_worker(agent: Agent, worker_task: str):
            if agent.status.value == "created":
                await agent.start()
            return await agent.run(worker_task, context)

        tasks = [
            run_worker(agent, worker_task)
            for agent, worker_task in zip(self.workers, worker_tasks)
        ]
        worker_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect worker results
        worker_results = []
        for agent, response in zip(self.workers, worker_responses):
            if isinstance(response, Exception):
                worker_results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": None,
                    "success": False,
                    "error": str(response)
                })
            else:
                worker_results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": response.output,
                    "success": response.success
                })

        # Supervisor aggregates results
        supervisor_context = {
            **context,
            "worker_results": worker_results
        }
        final_response = await self.supervisor.run(
            f"Aggregate the following worker results and provide a final answer: {worker_results}",
            supervisor_context
        )

        return {
            "team_id": self.id,
            "team_name": self.name,
            "pattern": self.pattern.value,
            "task": task,
            "supervisor": {
                "agent_id": self.supervisor.id,
                "agent_name": self.supervisor.name,
                "plan": plan_response.output
            },
            "worker_results": worker_results,
            "final_output": final_response.output,
            "success": final_response.success
        }

    async def _execute_debate(
        self,
        task: str,
        context: Dict
    ) -> Dict:
        """Execute debate - agents discuss and vote on best answer."""
        if len(self.agents) < 2:
            # Not enough agents for debate
            return await self._execute_sequential(task, context)

        # Round 1: Each agent provides their initial answer
        round_1_responses = []
        for agent in self.agents.values():
            if agent.status.value == "created":
                await agent.start()

            response = await agent.run(task, context)
            round_1_responses.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "response": response.output,
                "confidence": response.metadata.get("confidence", 0.5)
            })

        # Round 2: Agents discuss and critique each other
        discussion_context = {
            **context,
            "responses": round_1_responses,
            "task": task
        }

        round_2_responses = []
        for agent in self.agents.values():
            critique_prompt = f"""Given these responses to the task '{task}':
{json.dumps(round_1_responses, indent=2)}

Provide your analysis and final answer:"""
            response = await agent.run(critique_prompt, discussion_context)
            round_2_responses.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "final_response": response.output
            })

        # Vote/select best response (using confidence scores)
        best_response = self._select_best_response(round_2_responses)

        return {
            "team_id": self.id,
            "team_name": self.name,
            "pattern": self.pattern.value,
            "task": task,
            "round_1_responses": round_1_responses,
            "round_2_responses": round_2_responses,
            "final_output": best_response,
            "success": True
        }

    def _distribute_task(self, task: str, num_workers: int) -> List[str]:
        """Distribute a task among workers."""
        # Simple distribution - split by sections or topics
        # In a real implementation, this would be more sophisticated
        return [task] * num_workers

    def _aggregate_results(self, results: List[Dict]) -> str:
        """Aggregate results from multiple agents."""
        if not results:
            return "No results to aggregate"

        # Simple aggregation - combine all outputs
        combined = []
        for r in results:
            combined.append(f"**{r.get('agent_name', 'Agent')}**: {r.get('output', '')}")

        return "\n\n".join(combined)

    def _select_best_response(self, responses: List[Dict]) -> str:
        """Select the best response from debate."""
        # Simple selection - return first response
        # In a real implementation, would use voting or scoring
        if responses:
            return responses[0].get("final_response", "No response")
        return "No responses"

    # ==================== Messaging ====================

    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: Any,
        message_type: str = "message"
    ) -> AgentMessage:
        """Send a message between agents."""
        sender = self.agents.get(sender_id)
        receiver = self.agents.get(receiver_id)

        if not sender or not receiver:
            raise ValueError("Invalid sender or receiver")

        message = AgentMessage(
            sender_id=sender_id,
            sender_name=sender.name,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )

        self.message_history.append(message)

        # Notify message handlers
        handlers = self._message_handlers.get(receiver_id, [])
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)

        return message

    def on_message(self, agent_id: str, handler: Callable):
        """Register a message handler for an agent."""
        if agent_id not in self._message_handlers:
            self._message_handlers[agent_id] = []
        self._message_handlers[agent_id].append(handler)

    # ==================== Serialization ====================

    def to_dict(self) -> Dict:
        """Serialize team to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern.value,
            "agents": [a.to_dict() for a in self.agents.values()],
            "supervisor_id": self.supervisor.id if self.supervisor else None,
            "worker_ids": [a.id for a in self.workers]
        }


# Global team registry
_teams: Dict[str, AgentTeam] = {}


def create_team(
    name: str,
    pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL
) -> AgentTeam:
    """Create a new agent team."""
    team = AgentTeam(name, pattern)
    _teams[team.id] = team
    return team


def get_team(team_id: str) -> Optional[AgentTeam]:
    """Get a team by ID."""
    return _teams.get(team_id)


def list_teams() -> List[Dict]:
    """List all teams."""
    return [team.to_dict() for team in _teams.values()]


# Helper to import json for debate function
import json