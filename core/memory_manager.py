"""
AgentOS - Memory Manager
Persistent and ephemeral memory with vector storage for AI agents
"""

import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import hashlib
import math


class VectorStore:
    """Simple vector storage with cosine similarity"""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self.vectors = {}  # id -> (vector, metadata)
        self.counter = 0

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate simple embedding from text hash (simulated)"""
        # Simple hash-based embedding for demonstration
        # In production, use sentence-transformers or similar
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Generate deterministic pseudo-embeddings
        seed = hash_val % (2**31)
        import random
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(self.dimensions)]

    def add(self, text: str, metadata: Dict = None) -> str:
        """Add text to vector store"""
        vector_id = f"vec_{uuid.uuid4().hex[:8]}"
        embedding = self._generate_embedding(text)
        self.vectors[vector_id] = {
            "embedding": embedding,
            "text": text,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        self.counter += 1
        return vector_id

    def search(self, query: str, top_k: int = 5, filter_func=None) -> List[Dict]:
        """Search for similar vectors"""
        query_embedding = self._generate_embedding(query)

        results = []
        for vec_id, data in self.vectors.items():
            if filter_func and not filter_func(data["metadata"]):
                continue

            similarity = self._cosine_similarity(query_embedding, data["embedding"])
            results.append({
                "id": vec_id,
                "text": data["text"],
                "metadata": data["metadata"],
                "score": similarity,
                "timestamp": data["timestamp"]
            })

        # Sort by similarity
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0
        return dot / (mag_a * mag_b)

    def delete(self, vec_id: str) -> bool:
        """Delete vector by ID"""
        if vec_id in self.vectors:
            del self.vectors[vec_id]
            return True
        return False

    def get(self, vec_id: str) -> Optional[Dict]:
        """Get vector by ID"""
        return self.vectors.get(vec_id)

    def count(self) -> int:
        """Get total count"""
        return len(self.vectors)

    def clear(self):
        """Clear all vectors"""
        self.vectors.clear()


class SemanticMemory:
    """Long-term semantic memory"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.facts = {}  # fact_id -> fact data
        self.concepts = defaultdict(set)  # concept -> set of fact_ids

    def store_fact(self, fact: str, concepts: List[str] = None,
                   metadata: Dict = None) -> str:
        """Store a fact in semantic memory"""
        fact_id = f"fact_{uuid.uuid4().hex[:8]}"

        # Add to vector store
        vec_id = self.vector_store.add(fact, {
            "type": "semantic",
            "fact_id": fact_id
        })

        # Store fact
        self.facts[fact_id] = {
            "id": fact_id,
            "fact": fact,
            "concepts": concepts or [],
            "vector_id": vec_id,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": None
        }

        # Index by concepts
        for concept in (concepts or []):
            self.concepts[concept.lower()].add(fact_id)

        return fact_id

    def retrieve_facts(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve facts similar to query"""
        results = self.vector_store.search(query, top_k)

        retrieved = []
        for r in results:
            fact_id = r["metadata"].get("fact_id")
            if fact_id and fact_id in self.facts:
                fact = self.facts[fact_id]
                fact["access_count"] += 1
                fact["last_accessed"] = datetime.now().isoformat()
                retrieved.append({
                    "fact": fact["fact"],
                    "concepts": fact["concepts"],
                    "score": r["score"],
                    "metadata": fact["metadata"]
                })

        return retrieved

    def get_facts_by_concept(self, concept: str) -> List[Dict]:
        """Get all facts related to a concept"""
        concept_ids = self.concepts.get(concept.lower(), set())
        return [self.facts[fid] for fid in concept_ids if fid in self.facts]

    def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact"""
        if fact_id not in self.facts:
            return False

        fact = self.facts[fact_id]

        # Remove from vector store
        vec_id = fact.get("vector_id")
        if vec_id:
            self.vector_store.delete(vec_id)

        # Remove from concepts index
        for concept in fact.get("concepts", []):
            if concept.lower() in self.concepts:
                self.concepts[concept.lower()].discard(fact_id)

        del self.facts[fact_id]
        return True

    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "total_facts": len(self.facts),
            "total_concepts": len(self.concepts),
            "vector_store_size": self.vector_store.count()
        }


class EpisodicMemory:
    """Short-term episodic memory for conversations and events"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.episodes = {}  # episode_id -> episode data
        self.sessions = {}  # session_id -> session data

    def create_session(self, agent_id: str, context: Dict = None) -> str:
        """Create new session"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = {
            "id": session_id,
            "agent_id": agent_id,
            "context": context or {},
            "episodes": [],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }
        return session_id

    def add_episode(self, session_id: str, episode_type: str,
                    content: str, metadata: Dict = None) -> str:
        """Add episode to session"""
        if session_id not in self.sessions:
            return None

        episode_id = f"ep_{uuid.uuid4().hex[:8]}"

        # Add to vector store
        vec_id = self.vector_store.add(content, {
            "type": "episodic",
            "episode_id": episode_id,
            "session_id": session_id
        })

        episode = {
            "id": episode_id,
            "type": episode_type,  # message, action, tool_call, result, error
            "content": content,
            "vector_id": vec_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        self.episodes[episode_id] = episode
        self.sessions[session_id]["episodes"].append(episode_id)
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
        self.sessions[session_id]["message_count"] += 1

        return episode_id

    def get_session_history(self, session_id: str,
                           limit: int = 50) -> List[Dict]:
        """Get session conversation history"""
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        episode_ids = session["episodes"][-limit:]

        return [
            self.episodes[eid]
            for eid in episode_ids
            if eid in self.episodes
        ]

    def search_episodes(self, query: str, session_id: str = None,
                       top_k: int = 5) -> List[Dict]:
        """Search episodes"""
        def filter_func(metadata):
            if session_id and metadata.get("session_id") != session_id:
                return False
            return metadata.get("type") == "episodic"

        results = self.vector_store.search(query, top_k, filter_func)

        retrieved = []
        for r in results:
            episode_id = r["metadata"].get("episode_id")
            if episode_id and episode_id in self.episodes:
                retrieved.append({
                    "episode": self.episodes[episode_id],
                    "score": r["score"]
                })

        return retrieved

    def close_session(self, session_id: str) -> bool:
        """Close session"""
        if session_id not in self.sessions:
            return False

        self.sessions[session_id]["closed_at"] = datetime.now().isoformat()
        self.sessions[session_id]["status"] = "closed"
        return True

    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get session statistics"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "message_count": session["message_count"],
            "episode_count": len(session["episodes"]),
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "status": session.get("status", "active")
        }

    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        return [
            {"id": sid, "agent_id": s["agent_id"],
             "message_count": s["message_count"]}
            for sid, s in self.sessions.items()
            if s.get("status") != "closed"
        ]


class ContextManager:
    """Manages context window and summarization"""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.token_estimate = 4  # rough estimate: 1 token ~= 4 chars

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // self.token_estimate

    def summarize_if_needed(self, content: List[Dict],
                           preserve_recent: int = 10) -> Tuple[str, List[Dict]]:
        """Summarize content if it exceeds token limit"""
        if not content:
            return "", []

        # Calculate total tokens
        total_text = " ".join(c.get("content", "") for c in content)
        total_tokens = self.estimate_tokens(total_text)

        if total_tokens <= self.max_tokens:
            return total_text, content

        # Keep recent items, summarize older ones
        recent = content[-preserve_recent:]
        older = content[:-preserve_recent]

        # Create summary of older content
        summary = self._create_summary(older)

        return summary, [{"type": "summary", "content": summary}] + recent

    def _create_summary(self, items: List[Dict]) -> str:
        """Create summary of items"""
        if not items:
            return ""

        item_types = defaultdict(int)
        for item in items:
            item_types[item.get("type", "unknown")] += 1

        type_summary = ", ".join(f"{count} {t}s"
                                 for t, count in item_types.items())

        return f"[Previous context: {type_summary}]"


class WorkingMemory:
    """Short-term working memory for current task"""

    def __init__(self):
        self.data = {}
        self.timestamps = {}

    def set(self, key: str, value: Any):
        """Set working memory value"""
        self.data[key] = value
        self.timestamps[key] = datetime.now().isoformat()

    def get(self, key: str, default: Any = None) -> Any:
        """Get working memory value"""
        return self.data.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete working memory value"""
        if key in self.data:
            del self.data[key]
            if key in self.timestamps:
                del self.timestamps[key]
            return True
        return False

    def clear(self):
        """Clear all working memory"""
        self.data.clear()
        self.timestamps.clear()

    def keys(self) -> List[str]:
        """Get all keys"""
        return list(self.data.keys())

    def get_all(self) -> Dict:
        """Get all data with timestamps"""
        return {
            "data": self.data,
            "timestamps": self.timestamps
        }


class MemoryManager:
    """
    Unified Memory Manager
    Coordinates semantic, episodic, working, and context memory
    """

    def __init__(self, vector_dims: int = 384, max_context_tokens: int = 8000):
        # Initialize components
        self.vector_store = VectorStore(dimensions=vector_dims)
        self.semantic = SemanticMemory(self.vector_store)
        self.episodic = EpisodicMemory(self.vector_store)
        self.context = ContextManager(max_tokens=max_context_tokens)
        self.working = WorkingMemory()

        # Session mappings
        self.agent_sessions = {}  # agent_id -> session_id

    # ============== Semantic Memory ==============

    def store_knowledge(self, fact: str, concepts: List[str] = None,
                        metadata: Dict = None) -> str:
        """Store knowledge in semantic memory"""
        return self.semantic.store_fact(fact, concepts, metadata)

    def recall_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """Recall knowledge from semantic memory"""
        return self.semantic.retrieve_facts(query, top_k)

    def search_knowledge(self, concept: str) -> List[Dict]:
        """Search knowledge by concept"""
        return self.semantic.get_facts_by_concept(concept)

    # ============== Episodic Memory ==============

    def start_session(self, agent_id: str, context: Dict = None) -> str:
        """Start new agent session"""
        session_id = self.episodic.create_session(agent_id, context)
        self.agent_sessions[agent_id] = session_id
        return session_id

    def get_session(self, agent_id: str) -> Optional[str]:
        """Get current session for agent"""
        return self.agent_sessions.get(agent_id)

    def add_interaction(self, agent_id: str, interaction_type: str,
                        content: str, metadata: Dict = None) -> str:
        """Add interaction to session"""
        session_id = self.agent_sessions.get(agent_id)
        if not session_id:
            session_id = self.start_session(agent_id)

        return self.episodic.add_episode(session_id, interaction_type,
                                         content, metadata)

    def get_history(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for agent"""
        session_id = self.agent_sessions.get(agent_id)
        if not session_id:
            return []

        return self.episodic.get_session_history(session_id, limit)

    def end_session(self, agent_id: str) -> bool:
        """End agent session"""
        session_id = self.agent_sessions.get(agent_id)
        if session_id:
            self.episodic.close_session(session_id)
            if agent_id in self.agent_sessions:
                del self.agent_sessions[agent_id]
            return True
        return False

    # ============== Working Memory ==============

    def set_working(self, key: str, value: Any):
        """Set working memory"""
        self.working.set(key, value)

    def get_working(self, key: str, default: Any = None) -> Any:
        """Get working memory"""
        return self.working.get(key, default)

    def clear_working(self):
        """Clear working memory"""
        self.working.clear()

    # ============== Context ==============

    def build_context(self, agent_id: str, include_recent: int = 10) -> str:
        """Build context for agent"""
        # Get recent history
        history = self.get_history(agent_id, limit=include_recent + 20)

        # Summarize if needed
        summary, condensed = self.context.summarize_if_needed(
            history, preserve_recent=include_recent
        )

        # Get relevant semantic memories
        if history:
            last_content = history[-1].get("content", "")
            relevant_knowledge = self.recall_knowledge(last_content, top_k=3)
        else:
            relevant_knowledge = []

        # Build context string
        context_parts = []

        if relevant_knowledge:
            knowledge_str = "Relevant knowledge:\n" + "\n".join(
                f"- {k['fact']}" for k in relevant_knowledge
            )
            context_parts.append(knowledge_str)

        if summary:
            context_parts.append(f"Summary: {summary}")

        if condensed:
            recent_str = "Recent interactions:\n" + "\n".join(
                f"[{e.get('type', 'message')}] {e.get('content', '')}"
                for e in condensed[-include_recent:]
            )
            context_parts.append(recent_str)

        return "\n\n".join(context_parts)

    # ============== Statistics ==============

    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "semantic": self.semantic.get_stats(),
            "vector_store": {
                "total_vectors": self.vector_store.count()
            },
            "working_memory": {
                "keys": self.working.keys()
            },
            "active_sessions": len(self.episodic.get_active_sessions())
        }


# Singleton instance
memory_manager = MemoryManager()


def health_check() -> Dict:
    """Health check for memory manager"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "vector_store": memory_manager.vector_store.count(),
            "semantic_facts": len(memory_manager.semantic.facts),
            "episodic_episodes": len(memory_manager.episodic.episodes),
            "active_sessions": len(memory_manager.episodic.get_active_sessions())
        }
    }