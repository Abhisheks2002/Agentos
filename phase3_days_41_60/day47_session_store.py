"""
Day 47: Session Store (Redis-like)
===================================
Implement a session store similar to Redis for agent state management.

Sessions store ephemeral data like conversation history, user preferences,
and temporary agent state.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import json
import time


@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    data: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """
    Session Store (Redis-like)
    ==========================

    In-memory session storage with expiration support.

    Supported operations:
    - SET, GET, DELETE
    - SETEX (with expiration)
    - INCR, DECR
    - EXPIRE, TTL
    - KEYS, SCAN
    - Lists, Sets, Hashes

    Simulates Redis data structures for agent sessions.
    """

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._strings: Dict[str, Any] = {}
        self._lists: Dict[str, List[Any]] = {}
        self._sets: Dict[str, Set[Any]] = {}
        self._hashes: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, datetime] = {}

    # ========== String Operations ==========

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        nx: bool = False
    ) -> bool:
        """
        Set a key-value pair
        ====================

        SET key value [EX seconds] [NX]
        """
        if nx and key in self._strings:
            return False

        # Serialize if needed
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value)

        self._strings[key] = value

        if ttl:
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        elif key in self._expiry:
            del self._expiry[key]

        return True

    def get(self, key: str) -> Optional[Any]:
        """Get value by key (GET)"""
        if not self._is_valid(key):
            return None
        return self._strings.get(key)

    def mset(self, mapping: Dict[str, Any]) -> bool:
        """Set multiple keys (MSET)"""
        for key, value in mapping.items():
            self.set(key, value)
        return True

    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple keys (MGET)"""
        return [self.get(k) for k in keys]

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment value (INCR)"""
        current = self.get(key)
        if current is None:
            current = 0
        try:
            current = int(current)
        except (ValueError, TypeError):
            raise ValueError(f"Value at {key} is not an integer")

        new_value = current + amount
        self.set(key, str(new_value))
        return new_value

    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement value (DECR)"""
        return self.incr(key, -amount)

    def append(self, key: str, value: str) -> int:
        """Append to string (APPEND)"""
        current = self.get(key)
        if current is None:
            current = ""
        new_value = str(current) + value
        self.set(key, new_value)
        return len(new_value)

    def strlen(self, key: str) -> int:
        """Get string length (STRLEN)"""
        value = self.get(key)
        return len(str(value)) if value is not None else 0

    # ========== List Operations ==========

    def lpush(self, key: str, *values) -> int:
        """Push to left of list (LPUSH)"""
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key] = list(values) + self._lists[key]
        return len(self._lists[key])

    def rpush(self, key: str, *values) -> int:
        """Push to right of list (RPUSH)"""
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key].extend(values)
        return len(self._lists[key])

    def lpop(self, key: str) -> Optional[Any]:
        """Pop from left (LPOP)"""
        if key not in self._lists or not self._lists[key]:
            return None
        return self._lists[key].pop(0)

    def rpop(self, key: str) -> Optional[Any]:
        """Pop from right (RPOP)"""
        if key not in self._lists or not self._lists[key]:
            return None
        return self._lists[key].pop()

    def lrange(self, key: str, start: int = 0, stop: int = -1) -> List[Any]:
        """Get range of elements (LRANGE)"""
        if key not in self._lists:
            return []

        lst = self._lists[key]
        if stop == -1:
            stop = len(lst)
        return lst[start:stop]

    def llen(self, key: str) -> int:
        """Get list length (LLEN)"""
        return len(self._lists.get(key, []))

    # ========== Set Operations ==========

    def sadd(self, key: str, *members) -> int:
        """Add to set (SADD)"""
        if key not in self._sets:
            self._sets[key] = set()

        before = len(self._sets[key])
        self._sets[key].update(members)
        return len(self._sets[key]) - before

    def smembers(self, key: str) -> Set[Any]:
        """Get all members (SMEMBERS)"""
        return self._sets.get(key, set()).copy()

    def sismember(self, key: str, member: Any) -> bool:
        """Check membership (SISMEMBER)"""
        return member in self._sets.get(key, set())

    def scard(self, key: str) -> int:
        """Set cardinality (SCARD)"""
        return len(self._sets.get(key, set()))

    def spop(self, key: str) -> Optional[Any]:
        """Pop random member (SPOP)"""
        if key not in self._sets or not self._sets[key]:
            return None

        member = next(iter(self._sets[key]))
        self._sets[key].discard(member)
        return member

    # ========== Hash Operations ==========

    def hset(
        self,
        key: str,
        field: str = None,
        value: Any = None,
        mapping: Dict[str, Any] = None
    ) -> int:
        """
        Set hash field(s)
        =================

        HSET key field value
        HSET key mapping
        """
        if key not in self._hashes:
            self._hashes[key] = {}

        if mapping:
            before = len(self._hashes[key])
            self._hashes[key].update(mapping)
            return len(self._hashes[key]) - before

        if field is None or value is None:
            raise ValueError("field and value required")

        self._hashes[key][field] = value
        return 1

    def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field (HGET)"""
        return self._hashes.get(key, {}).get(field)

    def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields (HGETALL)"""
        return self._hashes.get(key, {}).copy()

    def hdel(self, key: str, *fields) -> int:
        """Delete hash fields (HDEL)"""
        if key not in self._hashes:
            return 0

        before = len(self._hashes[key])
        for field in fields:
            self._hashes[key].pop(field, None)

        return before - len(self._hashes[key])

    def hexists(self, key: str, field: str) -> bool:
        """Check field exists (HEXISTS)"""
        return field in self._hashes.get(key, {})

    def hlen(self, key: str) -> int:
        """Hash length (HLEN)"""
        return len(self._hashes.get(key, {}))

    # ========== Expiry Operations ==========

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration (EXPIRE)"""
        if key not in self._strings:
            return False

        self._expiry[key] = datetime.now() + timedelta(seconds=seconds)
        return True

    def ttl(self, key: str) -> int:
        """Get time to live (TTL)"""
        if key not in self._expiry:
            return -1  # No expiry
        if key not in self._strings:
            return -2  # Key doesn't exist

        remaining = (self._expiry[key] - datetime.now()).total_seconds()
        return max(0, int(remaining))

    def persist(self, key: str) -> bool:
        """Remove expiration (PERSIST)"""
        if key in self._expiry:
            del self._expiry[key]
            return True
        return False

    # ========== Key Operations ==========

    def keys(self, pattern: str = "*") -> List[str]:
        """
        Find keys matching pattern (KEYS)
        ================================

        Supports * and ? patterns
        """
        import fnmatch

        result = []
        for key in self._strings.keys():
            if fnmatch.fnmatch(key, pattern):
                result.append(key)
        return result

    def delete(self, *keys) -> int:
        """Delete keys (DEL)"""
        count = 0
        for key in keys:
            if key in self._strings:
                del self._strings[key]
                count += 1
            if key in self._expiry:
                del self._expiry[key]
            if key in self._lists:
                del self._lists[key]
            if key in self._sets:
                del self._sets[key]
            if key in self._hashes:
                del self._hashes[key]
        return count

    def exists(self, *keys) -> int:
        """Check if keys exist (EXISTS)"""
        return sum(1 for k in keys if k in self._strings)

    def _is_valid(self, key: str) -> bool:
        """Check if key exists and not expired"""
        if key not in self._strings:
            return False

        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                # Auto-delete expired
                self.delete(key)
                return False

        return True

    def flush(self):
        """Clear all data (FLUSHDB)"""
        self._strings.clear()
        self._lists.clear()
        self._sets.clear()
        self._hashes.clear()
        self._expiry.clear()

    def info(self) -> Dict[str, Any]:
        """Get server info"""
        return {
            "strings": len(self._strings),
            "lists": len(self._lists),
            "sets": len(self._sets),
            "hashes": len(self._hashes),
            "total_keys": len(self._strings)
        }


# Session-specific wrapper
class AgentSessionStore:
    """
    Agent Session Store
    ====================

    High-level session management for agents.
    """

    def __init__(self, store: SessionStore = None):
        self.store = store or SessionStore()

    def create_session(
        self,
        user_id: str,
        agent_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new session"""
        session_id = f"session:{uuid.uuid4().hex[:12]}"

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "created_at": time.time(),
            "message_count": 0,
            "metadata": metadata or {}
        }

        # Store session data
        self.store.hset(f"{session_id}:meta", mapping=session_data)
        self.store.set(f"{session_id}:history", json.dumps([]))
        self.store.expire(session_id, 86400)  # 24 hour TTL

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata"""
        return self.store.hgetall(f"{session_id}:meta")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """Add message to session history"""
        history_key = f"{session_id}:history"
        history = json.loads(self.store.get(history_key) or "[]")

        history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        self.store.set(history_key, json.dumps(history))

        # Increment message count
        self.store.hset(f"{session_id}:meta", "message_count", len(history))

        return True

    def get_history(
        self,
        session_id: str,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """Get session conversation history"""
        history_key = f"{session_id}:history"
        history = json.loads(self.store.get(history_key) or "[]")

        if limit:
            return history[-limit:]
        return history

    def delete_session(self, session_id: str) -> bool:
        """Delete session and all data"""
        keys = [
            f"{session_id}:meta",
            f"{session_id}:history"
        ]
        self.store.delete(*keys)
        return True


# Demo function
def demo():
    """Demonstrate Session Store"""
    print("=" * 60)
    print("  Session Store (Redis-like) Demo")
    print("=" * 60)

    store = SessionStore()

    # String operations
    print("\n1. String operations...")
    store.set("name", "AgentOS")
    store.set("version", "1.0")
    store.setex("temp_data", 60, "expires in 60s")

    print(f"   name: {store.get('name')}")
    print(f"   version: {store.get('version')}")

    # Counter
    print("\n2. Counter operations...")
    store.set("counter", "0")
    store.incr("counter")
    store.incr("counter")
    store.incr("counter")
    print(f"   counter: {store.get('counter')}")

    # List operations
    print("\n3. List operations...")
    store.rpush("messages", "Hello")
    store.rpush("messages", "World")
    store.lpush("messages", "Start")
    print(f"   messages: {store.lrange('messages')}")

    # Hash operations
    print("\n4. Hash operations...")
    store.hset("user:1", "name", "Alice")
    store.hset("user:1", "email", "alice@example.com")
    store.hset("user:1", mapping={"age": "28", "role": "engineer"})
    print(f"   user:1: {store.hgetall('user:1')}")

    # Set operations
    print("\n5. Set operations...")
    store.sadd("tags", "python", "ai", "agents", "llm")
    store.sadd("tags", "python", "fastapi")  # python already exists
    print(f"   tags: {store.smembers('tags')}")
    print(f"   has python: {store.sismember('tags', 'python')}")

    # Session store
    print("\n6. Agent Session Store...")
    session_store = AgentSessionStore(store)

    session_id = session_store.create_session(
        user_id="user123",
        agent_id="agent456",
        metadata={"source": "web"}
    )
    print(f"   Created session: {session_id}")

    session_store.add_message(session_id, "user", "Hello!")
    session_store.add_message(session_id, "assistant", "Hi there!")
    session_store.add_message(session_id, "user", "How are you?")

    history = session_store.get_history(session_id)
    print(f"   History ({len(history)} messages):")
    for msg in history:
        print(f"     {msg['role']}: {msg['content']}")

    # Info
    print("\n7. Store info:")
    info = store.info()
    print(f"   {info}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()