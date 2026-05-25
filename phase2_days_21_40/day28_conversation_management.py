"""
Day 28: Multi-Agent Conversation Management
============================================
Skill: Conversation Orchestration
Mini Project: Chat Manager

Managing complex multi-party conversations.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class ParticipantRole(str, Enum):
    """Roles in a conversation"""
    FACILITATOR = "facilitator"
    PARTICIPANT = "participant"
    OBSERVER = "observer"
    EXPERT = "expert"


class TurnType(str, Enum):
    """Types of conversation turns"""
    STATEMENT = "statement"
    QUESTION = "question"
    ANSWER = "answer"
    COMMAND = "command"
    REFLECTION = "reflection"
    SUMMARY = "summary"


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    speaker: str = ""
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    turn_type: TurnType = TurnType.STATEMENT
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reply_to: Optional[str] = None


@dataclass
class ConversationContext:
    """Shared context for a conversation"""
    topic: str = ""
    goal: Optional[str] = None
    history: List[ConversationTurn] = field(default_factory=list)
    participants: Dict[str, ParticipantRole] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)


class ConversationManager:
    """Manages multi-agent conversations"""

    def __init__(self, context: Optional[ConversationContext] = None):
        self.context = context or ConversationContext()
        self.turn_queue: asyncio.Queue = asyncio.Queue()
        self.listeners: Dict[str, Callable] = {}
        self.active = False
        self.turn_count = 0

    def add_participant(self, agent_id: str, role: ParticipantRole):
        """Add a participant to the conversation"""
        self.context.participants[agent_id] = role

    def remove_participant(self, agent_id: str):
        """Remove a participant"""
        self.context.participants.pop(agent_id, None)

    async def add_turn(self, turn: ConversationTurn):
        """Add a turn to the conversation"""
        self.context.history.append(turn)
        self.turn_count += 1

        # Notify listeners
        for listener in self.listeners.values():
            await listener(turn)

    async def get_recent_turns(self, count: int = 5) -> List[ConversationTurn]:
        """Get recent conversation turns"""
        return self.context.history[-count:]

    def get_participant_history(self, participant: str) -> List[ConversationTurn]:
        """Get all turns by a participant"""
        return [t for t in self.context.history if t.speaker == participant]

    async def summarize(self) -> str:
        """Generate conversation summary"""
        if not self.context.history:
            return "No conversation yet."

        turns = len(self.context.history)
        speakers = len(set(t.speaker for t in self.context.history))

        return f"Conversation: {turns} turns, {speakers} participants, topic: {self.context.topic}"


class TurnAllocator:
    """Allocates turns in a conversation"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.turn_order: List[str] = []
        self.current_index = 0

    def set_order(self, participants: List[str]):
        """Set the turn order"""
        self.turn_order = participants
        self.current_index = 0

    def next_turn(self) -> Optional[str]:
        """Get next participant"""
        if not self.turn_order:
            return None

        participant = self.turn_order[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.turn_order)
        return participant

    def who_speaks_next(self) -> Optional[str]:
        """Peek at next speaker without advancing"""
        if not self.turn_order:
            return None
        return self.turn_order[self.current_index]


class ConversationAnalyzer:
    """Analyzes conversation dynamics"""

    def __init__(self, context: ConversationContext):
        self.context = context

    def get_participation_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get participation statistics per participant"""
        stats = {}

        for turn in self.context.history:
            speaker = turn.speaker
            if speaker not in stats:
                stats[speaker] = {
                    "turns": 0,
                    "questions": 0,
                    "answers": 0,
                    "statements": 0
                }

            stats[speaker]["turns"] += 1

            if turn.turn_type == TurnType.QUESTION:
                stats[speaker]["questions"] += 1
            elif turn.turn_type == TurnType.ANSWER:
                stats[speaker]["answers"] += 1
            elif turn.turn_type == TurnType.STATEMENT:
                stats[speaker]["statements"] += 1

        return stats

    def get_conversation_flow(self) -> List[str]:
        """Get the flow of the conversation"""
        return [f"{t.speaker}: {t.turn_type.value}" for t in self.context.history]

    def find_agreements(self) -> List[Dict[str, Any]]:
        """Find points of agreement"""
        agreements = []

        # Simple agreement detection (content similarity)
        for i, turn1 in enumerate(self.context.history):
            for turn2 in self.context.history[i+1:]:
                if turn1.content.lower() in turn2.content.lower():
                    agreements.append({
                        "turn1": turn1.id,
                        "turn2": turn2.id,
                        "agreement": turn1.content
                    })

        return agreements


class Facilitator:
    """Facilitates conversation between agents"""

    def __init__(self, manager: ConversationManager):
        self.manager = manager
        self.allows_interruptions = True

    async def facilitate(self, task: str) -> Dict[str, Any]:
        """Facilitate a conversation"""
        # Set up context
        self.manager.context.goal = task

        # Run conversation
        results = {
            "task": task,
            "turns": 0,
            "summary": "",
            "success": False
        }

        # Simulate facilitation
        results["turns"] = len(self.manager.context.history)
        results["summary"] = await self.manager.summarize()
        results["success"] = results["turns"] > 0

        return results

    def suggest_next_speaker(self) -> Optional[str]:
        """Suggest who should speak next"""
        allocator = TurnAllocator()
        allocator.set_order(list(self.manager.context.participants.keys()))
        return allocator.who_speaks_next()


# Demo
def run_demo():
    print("=" * 70)
    print("Multi-Agent Conversation Management Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create conversation context
        context = ConversationContext(
            topic="AI Agent Design",
            goal="Discuss agent patterns"
        )

        # Create manager
        manager = ConversationManager(context)

        # Add participants
        manager.add_participant("Alice", ParticipantRole.EXPERT)
        manager.add_participant("Bob", ParticipantRole.PARTICIPANT)
        manager.add_participant("Carol", ParticipantRole.FACILITATOR)

        # Add turns
        print("\n[1] Conversation Turns")
        print("-" * 40)

        turns = [
            ConversationTurn(
                speaker="Alice",
                role=ParticipantRole.EXPERT,
                turn_type=TurnType.STATEMENT,
                content="ReAct pattern is useful for complex tasks"
            ),
            ConversationTurn(
                speaker="Bob",
                role=ParticipantRole.PARTICIPANT,
                turn_type=TurnType.QUESTION,
                content="How does reflection work?"
            ),
            ConversationTurn(
                speaker="Alice",
                role=ParticipantRole.EXPERT,
                turn_type=TurnType.ANSWER,
                content="Reflection lets agents evaluate their outputs"
            )
        ]

        for turn in turns:
            await manager.add_turn(turn)

        print(f"  Added {len(turns)} conversation turns")
        print(f"  Recent: {(await manager.get_recent_turns(2))[0].content[:40]}...")

        # Turn allocation
        print("\n[2] Turn Allocation")
        print("-" * 40)

        allocator = TurnAllocator()
        allocator.set_order(["Alice", "Bob", "Carol"])

        for i in range(5):
            speaker = allocator.next_turn()
            print(f"  Turn {i+1}: {speaker}")

        # Analysis
        print("\n[3] Conversation Analysis")
        print("-" * 40)

        analyzer = ConversationAnalyzer(context)
        stats = analyzer.get_participation_stats()

        for participant, data in stats.items():
            print(f"  {participant}: {data['turns']} turns")

        # Facilitator
        print("\n[4] Facilitation")
        print("-" * 40)

        facilitator = Facilitator(manager)
        result = await facilitator.facilitate("Design agent patterns")
        print(f"  Task: {result['task']}")
        print(f"  Turns: {result['turns']}")
        print(f"  Summary: {result['summary'][:50]}...")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()