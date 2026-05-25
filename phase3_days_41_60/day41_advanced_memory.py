"""
Day 41: Advanced Memory Systems - Long-Term Memory
====================================================
Skill: Memory Architecture
Mini Project: Persistent Memory Store

Advanced memory systems for AI agents with persistence,
retrieval, and forgetting capabilities.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json


class MemoryType(str, Enum):
    """Types of memory"""
    EPISODIC = "episodic"  # Specific experiences
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How to do things
    WORKING = "working"  # Short-term


@dataclass
class Memory:
    """Single memory unit"""
    id: str
    content: str
    memory_type: MemoryType
    importance: float = 0.5  # 0-1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    embeddings: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = f"mem_{uuid.uuid4().hex[:12]}"

    def access(self):
        """Record memory access"""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1

    def relevance_score(self, current_time: datetime = None) -> float:
        """Calculate relevance based on recency and importance"""
        if not current_time:
            current_time = datetime.now()

        created = datetime.fromisoformat(self.created_at)
        age = (current_time - created).total_seconds()

        # Decay based on age and importance
        decay = 0.99 ** (age / 3600)  # Hourly decay

        return self.importance * decay * (1 + 0.1 * self.access_count)


class VectorStore:
    """
    Vector Store for Memory Retrieval
    ==================================
    """

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self.vectors: Dict[str, List[float]] = {}
        self.memories: Dict[str, Memory] = {}

    def add(self, memory: Memory):
        """Add memory to store"""
        if not memory.embeddings:
            memory.embeddings = self._generate_embedding(memory.content)

        self.memories[memory.id] = memory
        self.vectors[memory.id] = memory.embeddings

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding (simplified)"""
        # In production: use OpenAI embeddings
        import hashlib
        hash_val = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_val[:self.dimensions]]

    def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories"""
        query_embedding = self._generate_embedding(query)

        similarities = []
        for mem_id, vector in self.vectors.items():
            sim = self._cosine_similarity(query_embedding, vector)
            if sim >= threshold:
                similarities.append((self.memories[mem_id], sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(x * x for x in b) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot / (mag_a * mag_b)


class MemoryManager:
    """
    Advanced Memory Manager
    ========================

    Manages multiple memory types with forgetting
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.working_memory: List[Memory] = []
        self.max_working_memory = 7  # Miller's magic number
        self.forgetting_threshold = 0.1

    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
        metadata: Dict[str, Any] = None
    ) -> Memory:
        """Store a memory"""
        memory = Memory(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )

        # Add to vector store
        self.vector_store.add(memory)

        # Add to working memory if episodic
        if memory_type == MemoryType.EPISODIC:
            self._add_to_working(memory)

        return memory

    def _add_to_working(self, memory: Memory):
        """Add to working memory with management"""
        self.working_memory.append(memory)

        # Keep within limit
        if len(self.working_memory) > self.max_working_memory:
            oldest = self.working_memory.pop(0)
            # In production: consolidate to long-term

    def recall(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Recall memories"""
        if memory_types is None:
            memory_types = list(MemoryType)

        # Search vector store
        results = self.vector_store.search(query, k=k * 2)

        # Filter by type and format
        memories = []
        for memory, score in results:
            if memory.memory_type in memory_types:
                memory.access()
                memories.append({
                    "memory": memory,
                    "relevance": score,
                    "type": memory.memory_type.value
                })

        return memories[:k]

    def get_working_memory(self) -> List[Memory]:
        """Get current working memory contents"""
        return list(reversed(self.working_memory))

    def consolidate(self) -> int:
        """Consolidate working memory to long-term"""
        consolidated = 0

        for memory in self.working_memory:
            # Check if should be forgotten
            if memory.relevance_score() < self.forgetting_threshold:
                # Mark for forgetting
                memory.metadata["forget_at"] = (
                    datetime.now() + timedelta(days=7)
                ).isoformat()
                consolidated += 1

        return consolidated


class ConversationBuffer:
    """
    Conversation Buffer for Agent Memory
    ======================================
    """

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })

        # Trim if needed
        self._trim()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages"""
        return self.messages

    def get_context(self, last_n: int = None) -> str:
        """Get messages as context string"""
        msgs = self.messages[-last_n:] if last_n else self.messages

        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in msgs
        ])

    def _trim(self):
        """Trim to max tokens"""
        while self._estimate_tokens() > self.max_tokens:
            if len(self.messages) <= 1:
                break
            self.messages.pop(0)

    def _estimate_tokens(self) -> int:
        """Rough token estimate"""
        return sum(
            len(msg["content"].split()) * 1.3
            for msg in self.messages
        )


# Demo
def run_demo():
    print("=" * 70)
    print("Advanced Memory Systems Demo")
    print("=" * 70)

    # Create memory manager
    manager = MemoryManager()

    # Store memories
    print("\n[1] Storing Memories")
    print("-" * 40)

    manager.store(
        "User prefers dark mode interface",
        MemoryType.SEMANTIC,
        importance=0.8
    )

    manager.store(
        "User asked about Python programming",
        MemoryType.EPISODIC,
        importance=0.6
    )

    manager.store(
        "How to calculate fibonacci sequence",
        MemoryType.PROCEDURAL,
        importance=0.7
    )

    print(f"  ✓ Stored 3 memories")

    # Recall
    print("\n[2] Recall Memories")
    print("-" * 40)

    results = manager.recall("programming", k=2)

    for r in results:
        print(f"  {r['type']}: {r['memory'].content[:40]}...")
        print(f"    Relevance: {r['relevance']:.3f}")

    # Working memory
    print("\n[3] Working Memory")
    print("-" * 40)

    working = manager.get_working_memory()
    print(f"  Items in working memory: {len(working)}")

    # Conversation buffer
    print("\n[4] Conversation Buffer")
    print("-" * 40)

    buffer = ConversationBuffer(max_tokens=200)

    buffer.add_message("user", "Hello!")
    buffer.add_message("assistant", "Hi! How can I help?")
    buffer.add_message("user", "I like Python")
    buffer.add_message("assistant", "Great! Python is awesome.")

    print(f"  Messages: {len(buffer.messages)}")
    print(f"  Context:\n{buffer.get_context()}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()