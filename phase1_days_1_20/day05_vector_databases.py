"""
Day 5: Introduction to Vector Databases
========================================
Skill: Embeddings & Vector Storage
Mini Project: Agent Memory Search

Converts text into vectors so agents can "remember" related concepts.
Manually calculates cosine similarity between vectors.
"""

import numpy as np
from typing import List, Tuple
import os

# Simple embedding simulation (in production, use OpenAI or other providers)
def simple_embedding(text: str) -> np.ndarray:
    """Create a simple hash-based embedding vector"""
    # Simple hash to create deterministic vectors
    import hashlib
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    # Create a 3D-like vector (simplified)
    np.random.seed(hash_val % (2**32))
    return np.random.randn(3).astype(np.float32)  # 3D vector for demo

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))

class AgentMemory:
    """Simple vector-based memory store for agents"""

    def __init__(self):
        self.memories = []

    def add_memory(self, agent_id: str, content: str):
        """Add a memory with embedding"""
        embedding = simple_embedding(content)
        self.memories.append({
            "agent_id": agent_id,
            "content": content,
            "embedding": embedding
        })

    def find_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, float, str]]:
        """Find most similar memories to a query"""
        query_embedding = simple_embedding(query)

        similarities = []
        for memory in self.memories:
            sim = cosine_similarity(query_embedding, memory['embedding'])
            similarities.append((memory['agent_id'], sim, memory['content']))

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

# Demo with OpenAI embeddings (when API key is available)
def get_openai_embedding(text: str, client) -> np.ndarray:
    """Get embedding using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)

def demo_manual_calculation():
    """Demo manual cosine similarity calculation"""
    print("=" * 60)
    print("Manual Cosine Similarity Demo")
    print("=" * 60)

    # Two 3D vectors
    v1 = np.array([1.0, 2.0, 3.0])
    v2 = np.array([1.0, 2.0, 3.0])
    v3 = np.array([1.0, -1.0, 0.0])

    sim_12 = cosine_similarity(v1, v2)
    sim_13 = cosine_similarity(v1, v3)

    print(f"v1 = {v1}")
    print(f"v2 = {v2}")
    print(f"v3 = {v3}")
    print(f"\nSimilarity(v1, v2) = {sim_12:.4f} (same direction)")
    print(f"Similarity(v1, v3) = {sim_13:.4f} (perpendicular)")

def demo_agent_memory():
    """Demo the Agent Memory system"""
    print("\n" + "=" * 60)
    print("Agent Memory Search Demo")
    print("=" * 60)

    memory = AgentMemory()

    # Add memories for different agents
    memories = [
        ("agent_001", "User prefers dark mode UI and wants email notifications"),
        ("agent_001", "User's name is John and he works in engineering"),
        ("agent_002", "Project deadline is next Friday for the AI feature"),
        ("agent_003", "Database schema needs to support millions of users"),
        ("agent_002", "User wants to export data as CSV files"),
    ]

    for agent_id, content in memories:
        memory.add_memory(agent_id, content)
        print(f"Added memory to {agent_id}: {content[:50]}...")

    # Search for similar memories
    print("\n" + "-" * 60)
    queries = [
        "What are user's UI preferences?",
        "When is the project due?",
        "How should data be exported?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = memory.find_similar(query, top_k=2)
        for agent_id, similarity, content in results:
            print(f"  -> {agent_id} (similarity: {similarity:.3f})")
            print(f"     {content}")

if __name__ == "__main__":
    demo_manual_calculation()
    demo_agent_memory()