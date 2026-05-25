"""
Day 46: Semantic Cache
======================
Implement a semantic cache for LLM responses to reduce costs and latency.

A semantic cache stores similar queries and their responses, enabling
the agent to return cached results for semantically similar inputs.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import uuid
import math


@dataclass
class CacheEntry:
    """A cached response"""
    id: str
    query: str
    query_embedding: List[float]
    response: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600  # 1 hour default
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)


class SemanticCache:
    """
    Semantic Cache for LLM Responses
    ==================================

    Caches LLM responses and retrieves them based on semantic similarity
    rather than exact match.

    Features:
    - Embedding-based similarity search
    - TTL support
    - Access statistics
    - Cache invalidation
    - Hit/miss tracking

    Use cases:
    - Reduce API costs by caching similar queries
    - Reduce latency by returning cached responses
    - Improve consistency across similar queries
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        max_entries: int = 10000,
        default_ttl: int = 3600
    ):
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.default_ttl = default_ttl

        self.entries: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def _compute_hash(self, text: str) -> str:
        """Compute hash of text"""
        return hashlib.sha256(text.encode()).hexdigest()

    def _embedding_simulate(self, text: str) -> List[float]:
        """
        Simulate embedding generation
        ==============================

        In production, use actual embedding models:
        - OpenAI text-embedding-ada-002
        - Cohere embeddings
        - Sentence transformers

        This simulates with a deterministic hash-based vector
        """
        # Simple hash to create pseudo-embeddings
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        # Convert hex to floats in range [-1, 1]
        embedding = []
        for i in range(0, len(hash_val), 8):
            chunk = hash_val[i:i+8]
            val = int(chunk, 16) / (16**8) * 2 - 1
            embedding.append(val)

        # Pad to fixed size
        while len(embedding) < 128:
            embedding.append(0.0)

        return embedding[:128]

    def _cosine_similarity(
        self,
        emb1: List[float],
        emb2: List[float]
    ) -> float:
        """Compute cosine similarity between embeddings"""
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = math.sqrt(sum(a * a for a in emb1))
        magnitude2 = math.sqrt(sum(b * b for b in emb2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get(
        self,
        query: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Get cached response for query
        ==============================

        Returns cached response if similar query exists, None otherwise
        """
        # Generate embedding
        query_embedding = self._embedding_simulate(query)

        best_match = None
        best_similarity = 0.0

        # Clean expired entries
        self._clean_expired()

        # Find best matching entry
        for entry in self.entries.values():
            if entry.is_expired():
                continue

            similarity = self._cosine_similarity(
                query_embedding,
                entry.query_embedding
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry

        # Check threshold
        if best_match and best_similarity >= self.similarity_threshold:
            # Update access stats
            best_match.access_count += 1
            best_match.last_accessed = datetime.now()

            self.hits += 1

            return (
                best_match.response,
                {
                    "cached": True,
                    "similarity": best_similarity,
                    "cache_id": best_match.id,
                    "created_at": best_match.created_at.isoformat(),
                    "access_count": best_match.access_count
                }
            )

        self.misses += 1
        return None

    def set(
        self,
        query: str,
        response: Any,
        ttl: int = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store query-response pair in cache
        ===================================

        Returns cache entry ID
        """
        # Generate embedding
        query_embedding = self._embedding_simulate(query)

        # Evict if at capacity
        if len(self.entries) >= self.max_entries:
            self._evict_lru()

        # Create entry
        entry = CacheEntry(
            id=f"cache_{uuid.uuid4().hex[:8]}",
            query=query,
            query_embedding=query_embedding,
            response=response,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl or self.default_ttl,
            metadata=metadata or {}
        )

        self.entries[entry.id] = entry
        return entry.id

    def invalidate(self, query: str = None, cache_id: str = None) -> int:
        """
        Invalidate cache entries
        ========================

        Returns number of entries invalidated
        """
        count = 0

        if cache_id and cache_id in self.entries:
            del self.entries[cache_id]
            count = 1

        if query:
            query_hash = self._compute_hash(query)
            to_delete = [
                eid for eid, e in self.entries.items()
                if self._compute_hash(e.query) == query_hash
            ]
            for eid in to_delete:
                del self.entries[eid]
            count += len(to_delete)

        return count

    def _clean_expired(self):
        """Remove expired entries"""
        expired = [
            eid for eid, e in self.entries.items()
            if e.is_expired()
        ]
        for eid in expired:
            del self.entries[eid]

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.entries:
            return

        lru_entry = min(
            self.entries.values(),
            key=lambda e: e.last_accessed
        )
        del self.entries[lru_entry.id]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "total_entries": len(self.entries),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total
        }

    def clear(self):
        """Clear all cache entries"""
        self.entries.clear()
        self.hits = 0
        self.misses = 0

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all cache entries"""
        return [
            {
                "id": e.id,
                "query": e.query,
                "response": e.response,
                "created_at": e.created_at.isoformat(),
                "access_count": e.access_count,
                "is_expired": e.is_expired()
            }
            for e in self.entries.values()
        ]


class SemanticCacheWithLLM:
    """
    Semantic Cache with LLM Integration
    =====================================

    Wraps the semantic cache with LLM call logic.
    """

    def __init__(self, cache: SemanticCache = None):
        self.cache = cache or SemanticCache()

    def query(
        self,
        query: str,
        llm_call_fn: callable,
        metadata: Dict[str, Any] = None
    ) -> Tuple[Any, bool]:
        """
        Query with cache
        ================

        - First checks cache
        - On miss, calls LLM and caches result
        - Returns (response, was_cached)
        """
        # Check cache
        cached = self.cache.get(query, metadata)

        if cached:
            response, cache_meta = cached
            return response, True

        # Call LLM (in production, this would be actual API call)
        response = llm_call_fn(query)

        # Cache result
        self.cache.set(query, response, metadata=metadata)

        return response, False


# Demo function
def demo():
    """Demonstrate Semantic Cache"""
    print("=" * 60)
    print("  Semantic Cache Demo")
    print("=" * 60)

    cache = SemanticCache(
        similarity_threshold=0.90,
        default_ttl=3600
    )

    print("\n1. Adding entries to cache...")

    # Simulated LLM responses
    responses = {
        "What is Python?": "Python is a high-level programming language...",
        "Explain machine learning": "Machine learning is a subset of AI...",
        "What is the capital of France?": "The capital of France is Paris.",
        "Tell me about neural networks": "Neural networks are computational models..."
    }

    for query, response in responses.items():
        cache_id = cache.set(query, response)
        print(f"   Cached: {query[:40]}...")

    # Query cache
    print("\n2. Testing cache hits...")

    test_queries = [
        "What is Python programming?",
        "What is the capital of France?",
        "Tell me about deep learning",  # Should miss
    ]

    for query in test_queries:
        result = cache.get(query)
        if result:
            response, meta = result
            print(f"\n   Query: {query}")
            print(f"   Cached: {meta['cached']}")
            print(f"   Similarity: {meta['similarity']:.3f}")
            print(f"   Response: {response[:50]}...")
        else:
            print(f"\n   Query: {query}")
            print(f"   Cached: False (miss)")

    # Stats
    print("\n3. Cache statistics:")
    stats = cache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1%}")

    # Integration demo
    print("\n4. With LLM integration:")

    llm_cache = SemanticCacheWithLLM(cache)

    call_count = 0

    def mock_llm(query):
        nonlocal call_count
        call_count += 1
        return f"LLM response for: {query}"

    # First call - will hit LLM
    response, cached = llm_cache.query("Hello world", mock_llm)
    print(f"   Call 1 - Cached: {cached}, LLM calls: {call_count}")

    # Second call - similar query - should hit cache
    response, cached = llm_cache.query("Hello there", mock_llm)
    print(f"   Call 2 - Cached: {cached}, LLM calls: {call_count}")

    # Different query
    response, cached = llm_cache.query("Different question", mock_llm)
    print(f"   Call 3 - Cached: {cached}, LLM calls: {call_count}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()