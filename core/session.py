"""
AgentOS - Session Management System
Manages agent sessions with tracking, expiration, and persistence
"""

import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable
from enum import Enum
import uuid


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"


class Session:
    """Represents a single agent session"""

    def __init__(self, agent_id: str, metadata: dict = None, session_timeout: int = 3600):
        """
        Initialize a new session

        Args:
            agent_id: ID of the agent owning this session
            metadata: Optional session metadata
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.session_id = f"session_{uuid.uuid4().hex[:12]}"
        self.agent_id = agent_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata = metadata or {}
        self.session_timeout = session_timeout
        self.status = SessionStatus.ACTIVE

    def update_activity(self):
        """Update the last activity timestamp to current time"""
        self.last_activity = datetime.now()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if session has expired based on inactivity timeout"""
        elapsed = datetime.now() - self.last_activity
        return elapsed.total_seconds() > self.session_timeout

    def get_duration(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.created_at).total_seconds()

    def get_idle_time(self) -> float:
        """Get idle time in seconds since last activity"""
        return (datetime.now() - self.last_activity).total_seconds()

    def set_idle(self):
        """Mark session as idle"""
        self.status = SessionStatus.IDLE

    def close(self):
        """Close the session"""
        self.status = SessionStatus.CLOSED

    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
            "duration_seconds": self.get_duration(),
            "idle_seconds": self.get_idle_time(),
            "is_expired": self.is_expired()
        }


class SessionEventEmitter:
    """Event emitter for session events"""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {
            "session_created": [],
            "session_updated": [],
            "session_deleted": [],
            "session_expired": []
        }

    def on(self, event: str, callback: Callable):
        """Register event listener"""
        if event in self._listeners:
            self._listeners[event].append(callback)

    def emit(self, event: str, session: Session):
        """Emit event to all listeners"""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    callback(session)
                except Exception as e:
                    print(f"Error in session event listener: {e}")

    def clear_listeners(self, event: str = None):
        """Clear listeners for specific event or all events"""
        if event:
            self._listeners[event] = []
        else:
            for key in self._listeners:
                self._listeners[key] = []


class SessionManager:
    """Manages all agent sessions with persistence and cleanup"""

    def __init__(self, session_timeout: int = 3600, max_sessions: int = 100,
                 storage_path: str = None):
        """
        Initialize session manager

        Args:
            session_timeout: Default session timeout in seconds
            max_sessions: Maximum number of concurrent sessions
            storage_path: Path for session persistence (optional)
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.max_sessions = max_sessions
        self.storage_path = storage_path
        self.events = SessionEventEmitter()
        self._lock = threading.RLock()

        # Load existing sessions if storage path provided
        if storage_path:
            self._ensure_storage_dir()
            self._load_sessions()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        if self.storage_path:
            dir_path = os.path.dirname(self.storage_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

    def _load_sessions(self):
        """Load sessions from storage file"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for session_data in data.get("sessions", []):
                    session = Session(
                        agent_id=session_data["agent_id"],
                        metadata=session_data.get("metadata", {}),
                        session_timeout=session_data.get("session_timeout", self.session_timeout)
                    )
                    session.session_id = session_data["session_id"]
                    session.created_at = datetime.fromisoformat(session_data["created_at"])
                    session.last_activity = datetime.fromisoformat(session_data["last_activity"])
                    session.status = SessionStatus(session_data.get("status", "active"))
                    self.sessions[session.session_id] = session
        except Exception as e:
            print(f"Error loading sessions: {e}")

    def _save_sessions(self):
        """Save sessions to storage file"""
        if not self.storage_path:
            return

        try:
            data = {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "agent_id": s.agent_id,
                        "created_at": s.created_at.isoformat(),
                        "last_activity": s.last_activity.isoformat(),
                        "status": s.status.value,
                        "metadata": s.metadata,
                        "session_timeout": s.session_timeout
                    }
                    for s in self.sessions.values()
                ]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def create_session(self, agent_id: str, metadata: dict = None) -> Optional[Session]:
        """
        Create a new session for an agent

        Args:
            agent_id: ID of the agent
            metadata: Optional session metadata

        Returns:
            Session object or None if max sessions reached
        """
        with self._lock:
            # Check max sessions limit
            if len(self.sessions) >= self.max_sessions:
                # Try to clean up expired sessions first
                self.cleanup_expired_sessions()
                if len(self.sessions) >= self.max_sessions:
                    return None

            session = Session(
                agent_id=agent_id,
                metadata=metadata,
                session_timeout=self.session_timeout
            )
            self.sessions[session.session_id] = session
            self._save_sessions()

            # Emit event
            self.events.emit("session_created", session)

            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_agent_sessions(self, agent_id: str) -> List[Session]:
        """Get all sessions for a specific agent"""
        return [s for s in self.sessions.values() if s.agent_id == agent_id]

    def update_session(self, session_id: str) -> bool:
        """
        Update session activity timestamp

        Args:
            session_id: ID of the session to update

        Returns:
            True if session was updated, False if not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
            self._save_sessions()
            self.events.emit("session_updated", session)
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: ID of the session to delete

        Returns:
            True if session was deleted, False if not found
        """
        session = self.sessions.pop(session_id, None)
        if session:
            session.close()
            self._save_sessions()
            self.events.emit("session_deleted", session)
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_ids.append(session_id)
                session.status = SessionStatus.EXPIRED
                self.events.emit("session_expired", session)

        for session_id in expired_ids:
            del self.sessions[session_id]

        if expired_ids:
            self._save_sessions()

        return len(expired_ids)

    def get_active_sessions(self) -> List[Session]:
        """Get all active (non-expired) sessions"""
        return [s for s in self.sessions.values() if not s.is_expired()]

    def get_session_count(self) -> int:
        """Get total number of sessions"""
        return len(self.sessions)

    def get_stats(self) -> dict:
        """Get session statistics"""
        active = self.get_active_sessions()
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active),
            "expired_sessions": len(self.sessions) - len(active),
            "max_sessions": self.max_sessions,
            "by_agent": self._get_sessions_by_agent()
        }

    def _get_sessions_by_agent(self) -> Dict[str, int]:
        """Get session count grouped by agent"""
        counts = {}
        for session in self.sessions.values():
            counts[session.agent_id] = counts.get(session.agent_id, 0) + 1
        return counts


# Default session manager instance
_default_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create default session manager"""
    global _default_manager
    if _default_manager is None:
        _default_manager = SessionManager()
    return _default_manager


def init_session_manager(session_timeout: int = 3600, max_sessions: int = 100,
                         storage_path: str = None) -> SessionManager:
    """Initialize the default session manager with custom settings"""
    global _default_manager
    _default_manager = SessionManager(
        session_timeout=session_timeout,
        max_sessions=max_sessions,
        storage_path=storage_path
    )
    return _default_manager