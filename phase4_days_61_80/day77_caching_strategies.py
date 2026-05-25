"""
Day 77: Caching Strategies
===========================
Advanced caching for AI agent responses and data.

Key Concepts:
- Memory cache
- TTL expiration
- LRU eviction
- Cache invalidation
- Distributed cache
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json
import time
import threading


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hits: int = 0
    last_accessed: datetime = None

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class LRUCache:
    """
    LRU (Least Recently Used) Cache
    ==================================

    In-memory cache with LRU eviction policy.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                self.stats["expirations"] += 1
                self.stats["misses"] += 1
                return None

            # Update access order and hit count
            entry.hits += 1
            entry.last_accessed = datetime.now()
            self.cache.move_to_end(key)

            self.stats["hits"] += 1
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        expires_at: datetime = None
    ):
        """Set value in cache"""
        with self._lock:
            ttl = ttl if ttl is not None else self.default_ttl
            expires = None

            if ttl:
                expires = datetime.now() + timedelta(seconds=ttl)
            elif expires_at:
                expires = expires_at

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires,
                last_accessed=datetime.now()
            )

            # Evict if at capacity
            if key not in self.cache and len(self.cache) >= self.max_size:
                self._evict_lru()

            self.cache[key] = entry

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1

    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self.stats["evictions"],
                "expirations": self.stats["expirations"]
            }

    def keys(self) -> List[str]:
        """Get all keys"""
        return list(self.cache.keys())

    def values(self) -> List[Any]:
        """Get all values"""
        return [entry.value for entry in self.cache.values()]


class CacheKeyGenerator:
    """
    Cache Key Generator
    ===================

    Generate consistent cache keys.
    """

    @staticmethod
    def generate(*args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    @staticmethod
    def generate_agent_key(agent_id: str, prompt: str, context: Dict = None) -> str:
        """Generate key for agent response"""
        parts = [agent_id, prompt]
        if context:
            parts.append(json.dumps(context, sort_keys=True))
        return CacheKeyGenerator.generate(*parts)


class CacheWithFallback:
    """
    Cache with Fallback
    ====================

    Cache with primary and secondary storage.
    """

    def __init__(self, primary: LRUCache, secondary: LRUCache = None):
        self.primary = primary
        self.secondary = secondary

    def get(self, key: str) -> Optional[Any]:
        """Get value with fallback"""
        # Try primary
        value = self.primary.get(key)
        if value is not None:
            return value

        # Try secondary
        if self.secondary:
            value = self.secondary.get(key)
            if value is not None:
                # Promote to primary
                self.primary.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in both caches"""
        self.primary.set(key, value, ttl)
        if self.secondary:
            self.secondary.set(key, value, ttl)

    def invalidate(self, key: str):
        """Invalidate in both caches"""
        self.primary.delete(key)
        if self.secondary:
            self.secondary.delete(key)


class SemanticCache:
    """
    Semantic Cache
    ==============

    Cache for AI agent responses with semantic similarity.
    """

    def __init__(self, max_size: int = 500, similarity_threshold: float = 0.9):
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, prompt: str) -> str:
        """Normalize prompt to cache key"""
        return prompt.lower().strip()

    def _calculate_similarity(self, prompt1: str, prompt2: str) -> float:
        """Calculate semantic similarity (simplified)"""
        # Simple word-based similarity
        words1 = set(prompt1.lower().split())
        words2 = set(prompt2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get(self, prompt: str) -> Optional[Any]:
        """Get cached response with semantic matching"""
        normalized = self._normalize_key(prompt)

        for cached_key, entry in self.cache.items():
            similarity = self._calculate_similarity(prompt, cached_key)
            if similarity >= self.similarity_threshold:
                entry["hits"] += 1
                return entry["response"]

        return None

    def set(self, prompt: str, response: Any):
        """Cache response"""
        normalized = self._normalize_key(prompt)

        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            # Remove least hit entry
            least_hit = min(self.cache.items(), key=lambda x: x[1]["hits"])
            del self.cache[least_hit[0]]

        self.cache[normalized] = {
            "prompt": prompt,
            "response": response,
            "hits": 1,
            "created_at": datetime.now()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_hits": sum(e["hits"] for e in self.cache.values())
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Day 77: Caching Strategies")
    print("=" * 70)

    # Create LRU cache
    print("\n[1] LRU Cache")
    print("-" * 40)

    cache = LRUCache(max_size=3, default_ttl=10)

    cache.set("user:1", {"name": "Alice", "role": "admin"})
    cache.set("user:2", {"name": "Bob", "role": "user"})
    cache.set("user:3", {"name": "Charlie", "role": "user"})

    print("  Set 3 entries (capacity: 3)")

    # Access first entry (makes it most recently used)
    value = cache.get("user:1")
    print(f"  Get user:1: {value['name']}")

    # Add new entry (should evict LRU - user:2)
    cache.set("user:4", {"name": "Diana", "role": "user"})
    print("  Added 4th entry (evicts LRU)")

    print(f"  Keys: {cache.keys()}")

    stats = cache.get_stats()
    print(f"  Stats: Hits={stats['hits']}, Misses={stats['misses']}, Evictions={stats['evictions']}")

    # Cache with TTL
    print("\n[2] TTL Cache")
    print("-" * 40)

    ttl_cache = LRUCache(max_size=10, default_ttl=1)
    ttl_cache.set("temp:data", "temporary value", ttl=1)

    # Immediate get
    value = ttl_cache.get("temp:data")
    print(f"  Immediate get: {value}")

    # Wait for expiration
    time.sleep(1.1)
    value = ttl_cache.get("temp:data")
    print(f"  After TTL: {value}")

    # Cache key generator
    print("\n[3] Cache Key Generator")
    print("-" * 40)

    key1 = CacheKeyGenerator.generate_agent_key("agent-1", "Summarize this text", {"max_length": 100})
    key2 = CacheKeyGenerator.generate_agent_key("agent-1", "Summarize this text", {"max_length": 100})
    key3 = CacheKeyGenerator.generate_agent_key("agent-1", "Summarize this text", {"max_length": 200})

    print(f"  Same prompt/same params: {key1[:16]}... == {key2[:16]}... : {key1 == key2}")
    print(f"  Same prompt/diff params: {key1[:16]}... == {key3[:16]}... : {key1 == key3}")

    # Semantic cache
    print("\n[4] Semantic Cache")
    print("-" * 40)

    semantic_cache = SemanticCache(max_size=10, similarity_threshold=0.7)

    semantic_cache.set("what is machine learning", "Machine learning is...")
    semantic_cache.set("explain neural networks", "Neural networks are...")

    result = semantic_cache.get("what is machine learning?")
    print(f"  Exact match: {result[:20]}...")

    result = semantic_cache.get("machine learning explained")
    print(f"  Semantic match: {result[:20]}...")

    result = semantic_cache.get("what is python")
    print(f"  No match: {result}")

    # Cache with fallback
    print("\n[5] Multi-Level Cache")
    print("-" * 40)

    primary = LRUCache(max_size=5)
    secondary = LRUCache(max_size=10)

    multi_cache = CacheWithFallback(primary, secondary)

    multi_cache.set("shared:data", "shared value")
    primary.set("primary:only", "primary only")

    print(f"  Shared in both: {multi_cache.get('shared:data')}")
    print(f"  Primary only: {multi_cache.get('primary:only')}")
    print(f"  Not in cache: {multi_cache.get('missing')}")

    print("\n[6] Cache Statistics")
    print("-" * 40)

    # Populate cache with more data
    for i in range(20):
        cache.set(f"item:{i}", f"value_{i}")

    stats = cache.get_stats()
    print(f"  Size: {stats['size']}/{stats['max_size']}")
    print(f"  Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate']*100:.1f}%")
    print(f"  Evictions: {stats['evictions']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()