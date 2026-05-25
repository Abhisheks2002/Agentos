"""Memory Layer - Vector database and memory management for agents."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Optional ChromaDB import
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Using in-memory storage.")


class VectorStore:
    """Vector store for semantic memory search."""

    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or "./agentos_memory"
        self._client = None
        self._collection = None
        self._initialize()

    def _initialize(self):
        """Initialize the vector store."""
        if CHROMADB_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory
                )
                self._collection = self._client.get_or_create_collection(
                    name="agent_memory",
                    metadata={"description": "AgentOS memory store"}
                )
                logger.info(f"ChromaDB initialized at {self.persist_directory}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self._client = None
                self._collection = None
        else:
            # Fallback to in-memory storage
            self._memory_store: Dict[str, Dict] = {}
            logger.warning("Using in-memory storage fallback")

    def add(
        self,
        id: str,
        embedding: List[float],
        document: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add a vector to the store."""
        if CHROMADB_AVAILABLE and self._collection:
            try:
                self._collection.add(
                    ids=[id],
                    embeddings=[embedding],
                    documents=[document],
                    metadatas=[metadata or {}]
                )
                return True
            except Exception as e:
                logger.error(f"Failed to add vector: {e}")
                return False
        else:
            # Fallback storage
            self._memory_store[id] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata or {}
            }
            return True

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if CHROMADB_AVAILABLE and self._collection:
            try:
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where
                )
                return self._format_results(results)
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return []
        else:
            # Fallback: return all (simple search)
            return list(self._memory_store.values())[:n_results]

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector by ID."""
        if CHROMADB_AVAILABLE and self._collection:
            try:
                results = self._collection.get(ids=[id])
                if results["ids"]:
                    return {
                        "id": results["ids"][0],
                        "document": results["documents"][0],
                        "metadata": results["metadatas"][0]
                    }
            except Exception as e:
                logger.error(f"Get failed: {e}")
        else:
            return self._memory_store.get(id)
        return None

    def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        if CHROMADB_AVAILABLE and self._collection:
            try:
                self._collection.delete(ids=[id])
                return True
            except Exception as e:
                logger.error(f"Delete failed: {e}")
                return False
        else:
            if id in self._memory_store:
                del self._memory_store[id]
                return True
        return False

    def _format_results(self, results) -> List[Dict[str, Any]]:
        """Format ChromaDB results."""
        formatted = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
        return formatted


class MemoryManager:
    """
    Manages agent memory including short-term, long-term, and working memory.
    """

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self.short_term: Dict[str, List[Dict]] = {}  # agent_id -> memories
        self.long_term: Dict[str, List[Dict]] = {}   # agent_id -> memories
        self.working: Dict[str, Dict] = {}            # agent_id -> working data

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text. In production, use a proper embedding model."""
        # Simple hash-based embedding fallback
        # In production: use sentence-transformers or OpenAI embeddings
        import hashlib
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        # Normalize to fixed-size vector
        embedding = []
        for i in range(384):  # Standard embedding size
            embedding.append(((hash_val >> i) % 2) * 2 - 1)
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        return [x / magnitude for x in embedding] if magnitude > 0 else embedding

    # --- Short-term Memory ---

    async def add_short_term(
        self,
        agent_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add to short-term (ephemeral) memory."""
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        memory = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        if agent_id not in self.short_term:
            self.short_term[agent_id] = []
        self.short_term[agent_id].append(memory)

        # Also add to vector store for semantic search
        embedding = self._generate_embedding(content)
        self.vector_store.add(
            id=memory_id,
            embedding=embedding,
            document=content,
            metadata={"agent_id": agent_id, "type": "short_term", **metadata or {}}
        )

        logger.info(f"Added short-term memory {memory_id} for agent {agent_id}")
        return memory_id

    async def get_short_term(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get short-term memories for an agent."""
        memories = self.short_term.get(agent_id, [])
        return memories[-limit:]

    async def clear_short_term(self, agent_id: str):
        """Clear short-term memory for an agent."""
        if agent_id in self.short_term:
            # Remove from vector store
            for mem in self.short_term[agent_id]:
                self.vector_store.delete(mem["id"])
            self.short_term[agent_id] = []
            logger.info(f"Cleared short-term memory for agent {agent_id}")

    # --- Long-term Memory ---

    async def add_long_term(
        self,
        agent_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add to long-term (persistent) memory."""
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        memory = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        if agent_id not in self.long_term:
            self.long_term[agent_id] = []
        self.long_term[agent_id].append(memory)

        # Add to vector store
        embedding = self._generate_embedding(content)
        self.vector_store.add(
            id=memory_id,
            embedding=embedding,
            document=content,
            metadata={"agent_id": agent_id, "type": "long_term", **metadata or {}}
        )

        logger.info(f"Added long-term memory {memory_id} for agent {agent_id}")
        return memory_id

    async def get_long_term(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get long-term memories for an agent."""
        memories = self.long_term.get(agent_id, [])
        return memories[-limit:]

    # --- Semantic Search ---

    async def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
        memory_type: str = None
    ) -> List[Dict]:
        """Search memories semantically."""
        query_embedding = self._generate_embedding(query)

        # Filter by agent_id and optionally by memory type
        where = {"agent_id": agent_id}
        if memory_type:
            where["type"] = memory_type

        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=limit,
            where=where
        )

        return results

    # --- Working Memory ---

    async def set_working(self, agent_id: str, key: str, value: Any):
        """Set working memory value."""
        if agent_id not in self.working:
            self.working[agent_id] = {}
        self.working[agent_id][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }

    async def get_working(self, agent_id: str, key: str = None) -> Any:
        """Get working memory value."""
        if agent_id not in self.working:
            return None
        if key:
            return self.working[agent_id].get(key, {}).get("value")
        return self.working[agent_id]

    async def clear_working(self, agent_id: str):
        """Clear working memory for an agent."""
        if agent_id in self.working:
            self.working[agent_id] = {}

    # --- Memory Consolidation ---

    async def consolidate(self, agent_id: str):
        """Consolidate short-term memories into long-term."""
        short_memories = self.short_term.get(agent_id, [])

        for memory in short_memories:
            await self.add_long_term(
                agent_id=agent_id,
                content=memory["content"],
                metadata={**memory["metadata"], "consolidated": True}
            )

        # Clear short-term after consolidation
        await self.clear_short_term(agent_id)
        logger.info(f"Consolidated memory for agent {agent_id}")


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
