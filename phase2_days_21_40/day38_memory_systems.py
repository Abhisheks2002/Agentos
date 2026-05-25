"""
Day 38: Memory Systems
======================
Skill: Memory Architecture
Mini Project: Hierarchical Memory

Building comprehensive memory systems for agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio
import uuid
from collections import deque


class MemoryType(str, Enum):
    """Types of memory"""
    EPISODIC = "episodic"      # Specific experiences
    SEMANTIC = "semantic"      # Facts and knowledge
    PROCEDURAL = "procedural" # Skills and procedures
    WORKING = "working"        # Current context
    SENSORY = "sensory"       # Raw perceptions


class MemoryImportance(str, Enum):
    """Memory importance levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Memory:
    """A memory item"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.EPISODIC
    importance: MemoryImportance = MemoryImportance.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def access(self):
        """Record memory access"""
        self.accessed_at = datetime.now().isoformat()
        self.access_count += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "type": self.memory_type.value,
            "importance": self.importance.value,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "tags": self.tags
        }


class SensoryMemory:
    """Short-term sensory memory (seconds)"""

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.timestamp: datetime = datetime.now()

    def store(self, perception: Any):
        """Store a perception"""
        self.buffer.append({
            "data": perception,
            "timestamp": datetime.now().isoformat()
        })

    def get_recent(self, count: int = 5) -> List[Any]:
        """Get recent perceptions"""
        return list(self.buffer)[-count:]

    def clear(self):
        """Clear sensory memory"""
        self.buffer.clear()


class WorkingMemory:
    """Working memory (minutes)"""

    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self.items: Dict[str, Any] = {}
        self.attention_focus: Optional[str] = None

    def store(self, key: str, value: Any, ttl: int = None):
        """Store in working memory"""
        self.items[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "ttl": ttl
        }

        # Evict if too many items
        if len(self.items) > self.max_items:
            # Remove oldest
            oldest_key = min(self.items.keys(), key=lambda k: self.items[k]["timestamp"])
            del self.items[oldest_key]

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve from working memory"""
        if key in self.items:
            item = self.items[key]
            # Check TTL
            if item["ttl"]:
                # Simplified TTL check
                return item["value"]
            return item["value"]
        return None

    def get_all(self) -> Dict[str, Any]:
        """Get all working memory items"""
        return {k: v["value"] for k, v in self.items.items()}

    def clear(self):
        """Clear working memory"""
        self.items.clear()
        self.attention_focus = None


class EpisodicMemory:
    """Long-term episodic memory (experiences)"""

    def __init__(self, max_memories: int = 1000):
        self.max_memories = max_memories
        self.memories: List[Memory] = []
        self._index: Dict[str, List[int]] = {}  # tag -> memory indices

    def store(self, content: str, memory_type: MemoryType = MemoryType.EPISODIC,
              importance: MemoryImportance = MemoryImportance.NORMAL,
              tags: List[str] = None, metadata: Dict = None) -> Memory:
        """Store an episodic memory"""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )

        self.memories.append(memory)

        # Index by tags
        for tag in memory.tags:
            if tag not in self._index:
                self._index[tag] = []
            self._index[tag].append(len(self.memories) - 1)

        # Evict if too many
        if len(self.memories) > self.max_memories:
            # Remove least important/accessed
            self.memories.pop(0)

        return memory

    def retrieve(self, query: str = None, tags: List[str] = None,
                 limit: int = 10, recency_weight: float = 0.3) -> List[Memory]:
        """Retrieve memories"""
        results = self.memories.copy()

        # Filter by tags
        if tags:
            matching = set()
            for tag in tags:
                if tag in self._index:
                    matching.update(self._index[tag])
            results = [self.memories[i] for i in matching if i < len(self.memories)]

        # Sort by importance and recency
        def score(m: Memory):
            imp_score = m.importance.value * (1 - recency_weight)
            recency_score = recency_weight * (1 / (1 + m.access_count))
            return imp_score + recency_score

        results.sort(key=score, reverse=True)

        return results[:limit]

    def get_recent(self, count: int = 10) -> List[Memory]:
        """Get recent memories"""
        return self.memories[-count:]


class SemanticMemory:
    """Long-term semantic memory (knowledge)"""

    def __init__(self):
        self.facts: Dict[str, Memory] = {}
        self.concepts: Dict[str, Dict] = {}

    def store_fact(self, fact: str, entity: str = None, relation: str = None) -> Memory:
        """Store a fact"""
        memory = Memory(
            content=fact,
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.HIGH,
            tags=[entity, relation] if entity or relation else []
        )

        key = entity or str(hash(fact))
        self.facts[key] = memory
        return memory

    def store_concept(self, name: str, definition: str, properties: Dict = None,
                     examples: List[str] = None) -> Dict:
        """Store a concept"""
        concept = {
            "name": name,
            "definition": definition,
            "properties": properties or {},
            "examples": examples or [],
            "created_at": datetime.now().isoformat()
        }

        self.concepts[name] = concept

        # Also store as fact
        self.store_fact(f"{name}: {definition}", name, "definition")

        return concept

    def get_fact(self, entity: str) -> Optional[Memory]:
        """Get a fact"""
        return self.facts.get(entity)

    def get_concept(self, name: str) -> Optional[Dict]:
        """Get a concept"""
        return self.concepts.get(name)

    def search(self, query: str) -> List[Any]:
        """Search semantic memory"""
        results = []
        query_lower = query.lower()

        # Search facts
        for fact in self.facts.values():
            if query_lower in fact.content.lower():
                results.append(fact)

        # Search concepts
        for concept in self.concepts.values():
            if query_lower in concept["definition"].lower():
                results.append(concept)

        return results


class ProceduralMemory:
    """Long-term procedural memory (skills)"""

    def __init__(self):
        self.skills: Dict[str, Dict] = {}
        self.procedures: Dict[str, Dict] = {}

    def store_skill(self, name: str, description: str, implementation: Callable,
                   parameters: List[str] = None) -> Dict:
        """Store a skill"""
        skill = {
            "name": name,
            "description": description,
            "implementation": implementation,
            "parameters": parameters or [],
            "usage_count": 0,
            "created_at": datetime.now().isoformat()
        }

        self.skills[name] = skill
        return skill

    def store_procedure(self, name: str, steps: List[Dict], conditions: Dict = None) -> Dict:
        """Store a procedure"""
        procedure = {
            "name": name,
            "steps": steps,
            "conditions": conditions or {},
            "execution_count": 0,
            "created_at": datetime.now().isoformat()
        }

        self.procedures[name] = procedure
        return procedure

    def get_skill(self, name: str) -> Optional[Dict]:
        """Get a skill"""
        if name in self.skills:
            self.skills[name]["usage_count"] += 1
        return self.skills.get(name)

    def get_procedure(self, name: str) -> Optional[Dict]:
        """Get a procedure"""
        if name in self.procedures:
            self.procedures[name]["execution_count"] += 1
        return self.procedures.get(name)

    def list_skills(self) -> List[str]:
        """List all skills"""
        return list(self.skills.keys())


class HierarchicalMemory:
    """Complete hierarchical memory system"""

    def __init__(self):
        self.sensory = SensoryMemory()
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()

    def perceive(self, data: Any):
        """Store sensory data"""
        self.sensory.store(data)

    def think(self, content: str, importance: MemoryImportance = MemoryImportance.NORMAL) -> Memory:
        """Store in episodic memory"""
        return self.episodic.store(content, importance=importance)

    def learn_fact(self, fact: str, entity: str = None) -> Memory:
        """Learn a fact"""
        return self.semantic.store_fact(fact, entity)

    def learn_concept(self, name: str, definition: str, **kwargs) -> Dict:
        """Learn a concept"""
        return self.semantic.store_concept(name, definition, **kwargs)

    def remember(self, query: str = None, tags: List[str] = None) -> List[Memory]:
        """Remember from episodic memory"""
        return self.episodic.retrieve(query, tags)

    def get_working(self, key: str) -> Any:
        """Get from working memory"""
        return self.working.retrieve(key)

    def set_working(self, key: str, value: Any, ttl: int = None):
        """Set in working memory"""
        self.working.store(key, value, ttl)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "sensory": len(list(self.sensory.buffer)),
            "working": len(self.working.items),
            "episodic": len(self.episodic.memories),
            "semantic_facts": len(self.semantic.facts),
            "semantic_concepts": len(self.semantic.concepts),
            "procedural_skills": len(self.procedural.skills),
            "procedural_procedures": len(self.procedural.procedures)
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Memory Systems Demo")
    print("=" * 70)

    # Test Hierarchical Memory
    print("\n[1] Hierarchical Memory")
    print("-" * 40)

    memory = HierarchicalMemory()

    # Sensory memory
    memory.perceive({"type": "vision", "data": "image"})
    memory.perceive({"type": "audio", "data": "speech"})
    print(f"  Sensory: {len(list(memory.sensory.buffer))} items")

    # Working memory
    memory.set_working("current_task", "analyze data")
    memory.set_working("user_query", "what is AI?")
    print(f"  Working: {memory.get_working('current_task')}")

    # Episodic memory
    memory.think("User asked about AI", MemoryImportance.HIGH)
    memory.think("Explained machine learning concepts", MemoryImportance.NORMAL)
    memory.think("User seemed satisfied", MemoryImportance.NORMAL)
    print(f"  Episodic: {len(memory.episodic.memories)} memories")

    # Semantic memory
    memory.learn_fact("AI stands for Artificial Intelligence", "AI")
    memory.learn_concept(
        "Machine Learning",
        "Systems that learn from data",
        properties={"type": "supervised", "examples": ["classification", "regression"]}
    )
    print(f"  Semantic: {len(memory.semantic.facts)} facts, {len(memory.semantic.concepts)} concepts")

    # Retrieval
    print("\n[2] Memory Retrieval")
    print("-" * 40)

    recent = memory.remember(limit=2)
    print(f"  Recent memories: {len(recent)}")

    # Stats
    print("\n[3] Memory Statistics")
    print("-" * 40)

    stats = memory.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()