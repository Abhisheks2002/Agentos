"""
Day 50: Session Context Management
===================================
Managing context across multiple sessions and conversation states.

Key Concepts:
- Session persistence
- Context serialization
- State management across interactions
- Session recovery and cleanup
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid
import hashlib


class SessionState(Enum):
    """Session lifecycle states"""
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


@dataclass
class ContextEntry:
    """A single context entry"""
    id: str
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


@dataclass
class Session:
    """A conversation session"""
    id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    state: SessionState = SessionState.ACTIVE
    context: List[ContextEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to the session"""
        entry = ContextEntry(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            metadata=metadata or {}
        )
        # Estimate tokens (rough approximation)
        entry.token_count = len(content.split()) + len(content) // 4
        self.context.append(entry)
        self.last_active = datetime.now()

    def get_context_window(self, max_tokens: int = 4000) -> List[ContextEntry]:
        """Get context within token limit"""
        total_tokens = 0
        result = []

        # Go from most recent to oldest
        for entry in reversed(self.context):
            if total_tokens + entry.token_count > max_tokens:
                break
            result.append(entry)
            total_tokens += entry.token_count

        return list(reversed(result))


class SessionContextManager:
    """
    Session Context Manager
    ======================

    Manages multiple sessions with persistent context.
    Handles session creation, recovery, and cleanup.
    """

    def __init__(self, max_sessions: int = 100, max_context_tokens: int = 4000):
        self.max_sessions = max_sessions
        self.max_context_tokens = max_context_tokens
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids

    def create_session(self, user_id: str, initial_context: str = None) -> Session:
        """Create a new session"""
        # Check max sessions limit
        if len(self.sessions) >= self.max_sessions:
            self._cleanup_idle_sessions()

        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = Session(id=session_id, user_id=user_id)

        if initial_context:
            session.add_message("system", initial_context)

        self.sessions[session_id] = session

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self.sessions.get(session_id)

    def get_user_active_session(self, user_id: str) -> Optional[Session]:
        """Get user's most recent active session"""
        session_ids = self.user_sessions.get(user_id, [])
        for sid in reversed(session_ids):
            session = self.sessions.get(sid)
            if session and session.state == SessionState.ACTIVE:
                return session
        return None

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict = None
    ) -> Optional[Session]:
        """Add a message to a session"""
        session = self.sessions.get(session_id)
        if session:
            session.add_message(role, content, metadata)
        return session

    def suspend_session(self, session_id: str) -> bool:
        """Suspend a session (idle state)"""
        session = self.sessions.get(session_id)
        if session:
            session.state = SessionState.SUSPENDED
            return True
        return False

    def resume_session(self, session_id: str) -> bool:
        """Resume a suspended session"""
        session = self.sessions.get(session_id)
        if session and session.state == SessionState.SUSPENDED:
            session.state = SessionState.ACTIVE
            session.last_active = datetime.now()
            return True
        return False

    def terminate_session(self, session_id: str) -> bool:
        """Terminate a session"""
        session = self.sessions.get(session_id)
        if session:
            session.state = SessionState.TERMINATED
            return True
        return False

    def serialize_session(self, session_id: str) -> Optional[Dict]:
        """Serialize session for persistence"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "id": session.id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "state": session.state.value,
            "context": [
                {
                    "id": c.id,
                    "role": c.role,
                    "content": c.content,
                    "timestamp": c.timestamp.isoformat(),
                    "metadata": c.metadata,
                    "token_count": c.token_count
                }
                for c in session.context
            ],
            "metadata": session.metadata
        }

    def deserialize_session(self, data: Dict) -> Session:
        """Deserialize session from data"""
        session = Session(
            id=data["id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            state=SessionState(data["state"]),
            metadata=data.get("metadata", {})
        )

        for c in data.get("context", []):
            entry = ContextEntry(
                id=c["id"],
                role=c["role"],
                content=c["content"],
                timestamp=datetime.fromisoformat(c["timestamp"]),
                metadata=c.get("metadata", {}),
                token_count=c.get("token_count", 0)
            )
            session.context.append(entry)

        self.sessions[session.id] = session

        if session.user_id not in self.user_sessions:
            self.user_sessions[session.user_id] = []
        if session.id not in self.user_sessions[session.user_id]:
            self.user_sessions[session.user_id].append(session.id)

        return session

    def _cleanup_idle_sessions(self, max_idle_minutes: int = 30):
        """Clean up idle sessions"""
        now = datetime.now()
        to_terminate = []

        for session_id, session in self.sessions.items():
            if session.state == SessionState.ACTIVE:
                idle_minutes = (now - session.last_active).total_seconds() / 60
                if idle_minutes > max_idle_minutes:
                    to_terminate.append(session_id)

        # Terminate oldest first
        for session_id in to_terminate[:10]:  # Clean up max 10 at a time
            self.sessions[session_id].state = SessionState.IDLE

    def get_stats(self) -> Dict:
        """Get session statistics"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": sum(
                1 for s in self.sessions.values()
                if s.state == SessionState.ACTIVE
            ),
            "total_messages": sum(
                len(s.context) for s in self.sessions.values()
            ),
            "total_tokens": sum(
                sum(e.token_count for e in s.context)
                for s in self.sessions.values()
            )
        }


# Demo function
def demo():
    """Demonstrate Session Context Management"""
    print("=" * 60)
    print("  Session Context Management Demo")
    print("=" * 60)

    # Create manager
    manager = SessionContextManager(max_context_tokens=200)

    # Create sessions
    print("\n1. Creating Sessions:")
    session1 = manager.create_session(
        "user_001",
        "You are a helpful coding assistant."
    )
    print(f"   Created session: {session1.id}")

    session2 = manager.create_session(
        "user_001",
        "You are a creative writing assistant."
    )
    print(f"   Created session: {session2.id}")

    # Add messages
    print("\n2. Adding Messages:")
    manager.add_message(
        session1.id,
        "user",
        "How do I create a Python class?"
    )
    print("   Added user question")

    manager.add_message(
        session1.id,
        "assistant",
        "To create a Python class, use the 'class' keyword..."
    )
    print("   Added assistant response")

    # Test context window
    print("\n3. Context Window:")
    for msg in session1.get_context_window():
        print(f"   [{msg.role}]: {msg.content[:40]}...")

    # Test serialization
    print("\n4. Serialization:")
    serialized = manager.serialize_session(session1.id)
    print(f"   Serialized keys: {list(serialized.keys())}")

    # Stats
    print("\n5. Statistics:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()