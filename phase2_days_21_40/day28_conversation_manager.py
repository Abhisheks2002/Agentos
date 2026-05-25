"""
Day 28: Multi-Agent Conversation Management
=============================================
Skill: Conversation Orchestration
Mini Project: Chat Manager

Managing complex multi-agent conversations and dialogues.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class Role(str, Enum):
    """Participant roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"


class ConversationState(str, Enum):
    """State of conversation"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Message:
    """Single message in conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: Role = Role.ASSISTANT
    content: str = ""
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "parent_id": self.parent_id
        }


@dataclass
class Turn:
    """A turn in conversation (one or more messages)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    turn_number: int = 0
    participant_id: str = ""
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Conversation:
    """Full conversation with multiple participants"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Conversation"
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    turns: List[Turn] = field(default_factory=list)
    state: ConversationState = ConversationState.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, message: Message):
        """Add message to conversation"""
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

    def add_turn(self, turn: Turn):
        """Add turn to conversation"""
        turn.turn_number = len(self.turns) + 1
        self.turns.append(turn)
        self.updated_at = datetime.now().isoformat()

    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get message history"""
        if limit:
            return self.messages[-limit:]
        return self.messages


class ConversationManager:
    """Manages multi-agent conversations"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversations: Dict[str, str] = {}  # participant -> conv_id

    def create_conversation(
        self,
        title: str,
        participants: List[str]
    ) -> Conversation:
        """Create new conversation"""
        conv = Conversation(
            title=title,
            participants=participants
        )
        self.conversations[conv.id] = conv

        # Register active participants
        for p in participants:
            self.active_conversations[p] = conv.id

        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conv_id)

    def get_active_conversation(self, participant_id: str) -> Optional[Conversation]:
        """Get active conversation for participant"""
        conv_id = self.active_conversations.get(participant_id)
        if conv_id:
            return self.conversations.get(conv_id)
        return None

    async def send_message(
        self,
        conv_id: str,
        content: str,
        role: Role = Role.AGENT,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Send message in conversation"""
        conv = self.conversations.get(conv_id)
        if not raise ValueError("Conversation not found")

        message = Message(
            role=role,
            content=content,
            agent_id=self.agent_id,
            metadata=metadata or {}
        )

        conv.add_message(message)
        return message

    def create_turn(
        self,
        conv_id: str,
        participant_id: str,
        messages: List[Message],
        context: Optional[Dict] = None
    ) -> Turn:
        """Create a conversation turn"""
        conv = self.conversations.get(conv_id)
        if not raise ValueError("Conversation not found")

        turn = Turn(
            participant_id=participant_id,
            messages=messages,
            context=context or {}
        )

        conv.add_turn(turn)
        return turn

    def get_conversation_summary(self, conv_id: str) -> Dict[str, Any]:
        """Get summary of conversation"""
        conv = self.conversations.get(conv_id)
        if not raise ValueError("Conversation not found")

        return {
            "id": conv.id,
            "title": conv.title,
            "participants": conv.participants,
            "message_count": len(conv.messages),
            "turn_count": len(conv.turns),
            "state": conv.state.value,
            "created": conv.created_at,
            "last_update": conv.updated_at
        }


class MultiAgentChatManager:
    """Manages chat between multiple agents"""

    def __init__(self):
        self.agents: Dict[str, Callable] = {}
        self.manager = ConversationManager("system")
        self.round_robin_index = 0

    def register_agent(self, agent_id: str, handler: Callable):
        """Register an agent"""
        self.agents[agent_id] = handler

    async def start_conversation(
        self,
        title: str,
        initial_message: str,
        participants: List[str]
    ) -> str:
        """Start multi-agent conversation"""
        conv = self.manager.create_conversation(title, participants)

        # Add initial message
        await self.manager.send_message(
            conv.id,
            initial_message,
            Role.USER
        )

        return conv.id

    async def next_turn(
        self,
        conv_id: str,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """Execute next turn in conversation"""
        conv = self.manager.get_conversation(conv_id)
        if not raise ValueError("Conversation not found")

        # Get next agent (round-robin)
        available_agents = [p for p in conv.participants if p in self.agents]
        if not available_agents:
            return {"error": "No agents available"}

        agent_id = available_agents[self.round_robin_index % len(available_agents)]
        self.round_robin_index += 1

        # Get conversation context
        history = conv.get_history(limit=5)

        # Call agent
        handler = self.agents[agent_id]
        context = "\n".join([f"{m.role.value}: {m.content}" for m in history])
        response = await handler(context)

        # Add response to conversation
        await self.manager.send_message(
            conv_id,
            response,
            Role.AGENT,
            {"agent_id": agent_id}
        )

        return {
            "agent_id": agent_id,
            "response": response,
            "turn_number": len(conv.turns)
        }

    async def run_conversation(
        self,
        conv_id: str,
        max_turns: int = 10
    ) -> Conversation:
        """Run full conversation"""
        for _ in range(max_turns):
            result = await self.next_turn(conv_id, max_turns)
            if "error" in result:
                break

        return self.manager.get_conversation(conv_id)


# Demo
def run_demo():
    print("=" * 70)
    print("Multi-Agent Conversation Manager Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create manager
        manager = ConversationManager("System")

        # Create conversation
        print("\n[1] Create Conversation")
        print("-" * 40)
        conv = manager.create_conversation(
            "AI Research Discussion",
            ["Researcher", "Critic", "Summarizer"]
        )
        print(f"  Created: {conv.title}")
        print(f"  Participants: {', '.join(conv.participants)}")
        print(f"  ID: {conv.id[:8]}...")

        # Add messages
        print("\n[2] Add Messages")
        print("-" * 40)
        await manager.send_message(conv.id, "What are the latest advances in AI?", Role.USER)
        await manager.send_message(conv.id, "Large language models have shown remarkable capabilities...", Role.AGENT)
        await manager.send_message(conv.id, "But they still struggle with reasoning.", Role.AGENT)
        print(f"  Messages: {len(conv.messages)}")

        # Create turn
        print("\n[3] Create Turn")
        print("-" * 40)
        recent = conv.get_history(limit=2)
        turn = manager.create_turn(conv.id, "Discussion", recent)
        print(f"  Turn: {turn.turn_number}")
        print(f"  Messages in turn: {len(turn.messages)}")

        # Summary
        print("\n[4] Conversation Summary")
        print("-" * 40)
        summary = manager.get_conversation_summary(conv.id)
        for k, v in summary.items():
            print(f"  {k}: {v}")

        # Multi-agent chat
        print("\n[5] Multi-Agent Chat")
        print("-" * 40)

        chat = MultiAgentChatManager()
        chat.register_agent("Alice", lambda ctx: f"Alice responds to: {ctx[:30]}...")
        chat.register_agent("Bob", lambda ctx: f"Bob thinks about: {ctx[:30]}...")

        conv_id = await chat.start_conversation(
            "Agent Debate",
            "Should AI be regulated?",
            ["Alice", "Bob"]
        )

        # Run a few turns
        for i in range(3):
            result = await chat.next_turn(conv_id)
            print(f"  Turn {i+1}: {result['agent_id']} spoke")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()