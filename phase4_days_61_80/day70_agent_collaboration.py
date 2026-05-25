"""
Day 70: Agent Collaboration Protocols
=====================================
Protocols for multi-agent collaboration and communication.

Key Concepts:
- Agent communication protocols
- Role assignment
- Task delegation
- Consensus mechanisms
"""

from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    DELEGATE = "delegate"
    COMPLETE = "complete"
    FAIL = "fail"
    VOTE = "vote"


class AgentRole(Enum):
    """Roles in collaboration"""
    COORDINATOR = "coordinator"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    FACILITATOR = "facilitator"


@dataclass
class Agent:
    """Agent participating in collaboration"""
    agent_id: str
    name: str
    capabilities: Set[str]
    role: AgentRole = AgentRole.CONTRIBUTOR
    current_task: str = None


@dataclass
class CollaborationMessage:
    """Message between agents"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    thread_id: str = None


@dataclass
class Task:
    """A collaborative task"""
    task_id: str
    description: str
    assigned_agents: List[str]
    status: str = "pending"
    result: Any = None
    dependencies: List[str] = field(default_factory=list)


class AgentProtocol:
    """
    Agent Communication Protocol
    ============================

    Base protocol for agent communication.
    """

    def __init__(self, agent: Agent):
        self.agent = agent
        self.inbox: List[CollaborationMessage] = []
        self.outbox: List[CollaborationMessage] = []
        self.handlers: Dict[MessageType, Callable] = {}
        self._lock = asyncio.Lock()

    async def send_message(
        self,
        receiver_id: str,
        message_type: MessageType,
        content: Dict[str, Any]
    ) -> CollaborationMessage:
        """Send a message to another agent"""
        async with self._lock:
            msg = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent.agent_id,
                receiver_id=receiver_id,
                message_type=message_type,
                content=content,
                thread_id=content.get("thread_id")
            )

            self.outbox.append(msg)
            return msg

    async def receive_message(self, message: CollaborationMessage):
        """Receive a message"""
        async with self._lock:
            self.inbox.append(message)

            # Handle message if handler exists
            handler = self.handlers.get(message.message_type)
            if handler:
                await handler(message)

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable
    ):
        """Register message handler"""
        self.handlers[message_type] = handler


class CollaborationSession:
    """
    Collaboration Session
    =====================

    Manages a group of agents working together.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agents: Dict[str, Agent] = {}
        self.protocols: Dict[str, AgentProtocol] = {}
        self.tasks: Dict[str, Task] = {}
        self.messages: List[CollaborationMessage] = []
        self._lock = asyncio.Lock()

    def add_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: Set[str],
        role: AgentRole = AgentRole.CONTRIBUTOR
    ) -> Agent:
        """Add agent to collaboration"""
        agent = Agent(
            agent_id=agent_id,
            name=name,
            capabilities=capabilities,
            role=role
        )

        self.agents[agent_id] = agent
        self.protocols[agent_id] = AgentProtocol(agent)
        return agent

    async def delegate_task(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task: Task
    ) -> bool:
        """Delegate task from one agent to another"""
        async with self._lock:
            if from_agent_id not in self.agents or to_agent_id not in self.agents:
                return False

            task.assigned_agents.append(to_agent_id)
            self.tasks[task.task_id] = task

            # Send delegation message
            protocol = self.protocols[from_agent_id]
            msg = await protocol.send_message(
                to_agent_id,
                MessageType.DELEGATE,
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "thread_id": self.session_id
                }
            )

            self.messages.append(msg)
            return True

    async def vote(
        self,
        proposal_id: str,
        agent_id: str,
        vote: bool,
        reason: str = ""
    ):
        """Cast a vote in consensus"""
        protocol = self.protocols[agent_id]

        # In a real system, votes would be collected and tallied
        vote_msg = await protocol.send_message(
            "coordinator",
            MessageType.VOTE,
            {
                "proposal_id": proposal_id,
                "vote": vote,
                "reason": reason
            }
        )

        self.messages.append(vote_msg)

    async def get_agent_messages(
        self,
        agent_id: str
    ) -> List[CollaborationMessage]:
        """Get all messages for an agent"""
        protocol = self.protocols.get(agent_id)
        if not protocol:
            return []

        return protocol.inbox.copy()

    async def complete_task(
        self,
        task_id: str,
        agent_id: str,
        result: Any
    ):
        """Mark task as completed"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = "completed"
                task.result = result

                # Notify all assigned agents
                for aid in task.assigned_agents:
                    if aid in self.protocols:
                        protocol = self.protocols[aid]
                        await protocol.send_message(
                            aid,
                            MessageType.COMPLETE,
                            {"task_id": task_id, "result": result}
                        )

    def get_status(self) -> Dict[str, Any]:
        """Get collaboration status"""
        return {
            "session_id": self.session_id,
            "agent_count": len(self.agents),
            "task_count": len(self.tasks),
            "completed_tasks": sum(
                1 for t in self.tasks.values() if t.status == "completed"
            ),
            "agents": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "role": a.role.value,
                    "capabilities": list(a.capabilities)
                }
                for a in self.agents.values()
            ]
        }


class CollaborationOrchestrator:
    """
    Collaboration Orchestrator
    ==========================

    Coordinates multi-agent collaboration workflows.
    """

    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}

    async def create_session(self, session_id: str) -> CollaborationSession:
        """Create new collaboration session"""
        session = CollaborationSession(session_id)
        self.sessions[session_id] = session
        return session

    async def start_collaboration(
        self,
        session_id: str,
        agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Start a collaboration workflow"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Add agents
        for agent_data in agents:
            session.add_agent(
                agent_data["agent_id"],
                agent_data["name"],
                set(agent_data["capabilities"]),
                AgentRole(agent_data.get("role", "contributor"))
            )

        # Assign coordinator
        coordinator_id = agents[0]["agent_id"]
        session.agents[coordinator_id].role = AgentRole.COORDINATOR

        # Create and assign tasks
        for task_data in tasks:
            task = Task(
                task_id=str(uuid.uuid4()),
                description=task_data["description"],
                assigned_agents=[]
            )

            # Delegate to appropriate agent based on capabilities
            for agent in session.agents.values():
                if task_data.get("required_capability") in agent.capabilities:
                    await session.delegate_task(
                        coordinator_id,
                        agent.agent_id,
                        task
                    )
                    break

        return session.get_status()


# Demo
async def main():
    print("=" * 60)
    print("Day 70: Agent Collaboration Protocols")
    print("=" * 60)

    orchestrator = CollaborationOrchestrator()

    # Create session
    session = await orchestrator.create_session("project_alpha")

    # Define agents
    agents = [
        {
            "agent_id": "agent_1",
            "name": "Coordinator",
            "capabilities": ["coordination", "planning"],
            "role": "coordinator"
        },
        {
            "agent_id": "agent_2",
            "name": "Data Analyst",
            "capabilities": ["analysis", "data_processing"]
        },
        {
            "agent_id": "agent_3",
            "name": "Coder",
            "capabilities": ["code_generation", "review"]
        }
    ]

    # Define tasks
    tasks = [
        {
            "description": "Analyze dataset and generate insights",
            "required_capability": "analysis"
        },
        {
            "description": "Generate code based on analysis",
            "required_capability": "code_generation"
        }
    ]

    # Start collaboration
    print("\nStarting collaboration session...")
    status = await orchestrator.start_collaboration("project_alpha", agents, tasks)
    print(f"  Session ID: {status['session_id']}")
    print(f"  Agents: {status['agent_count']}")
    print(f"  Tasks: {status['task_count']}")

    print("\nParticipants:")
    for agent in status["agents"]:
        print(f"  - {agent['name']} ({agent['role']})")

    # Complete a task
    await session.complete_task(
        list(session.tasks.keys())[0],
        "agent_2",
        {"insights": "Found 3 key patterns", "confidence": 0.95}
    )

    print("\nTask completed!")
    print(f"  Completed: {status['completed_tasks']}")


if __name__ == "__main__":
    asyncio.run(main())