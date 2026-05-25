"""
Day 5: Introduction to Vector Databases
=======================================
Skill: Embeddings & Vector Storage
Mini Project: Agent Memory Search

Converts text into vectors so agents can "remember" related concepts.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

# Simple embedding simulation (in production, use OpenAI or other embeddings)
def simple_embedding(text: str, dim: int = 3) -> np.ndarray:
    """Generate a simple deterministic embedding from text"""
    # Create a deterministic embedding based on text
    np.random.seed(hash(text) % (2**32))
    return np.random.randn(dim)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return float(dot_product / (norm_a * norm_b))

class AgentMemory:
    """Simple vector-based memory store for agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: List[Dict] = []

    def add_memory(self, content: str, metadata: Dict = None):
        """Add a memory with its embedding"""
        embedding = simple_embedding(content)
        memory = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.memories.append(memory)

    def search(self, query: str, top_k: int = 1) -> List[Dict]:
        """Find the most similar memory to a query"""
        if not self.memories:
            return []

        query_embedding = simple_embedding(query)

        # Calculate similarities
        similarities = []
        for memory in self.memories:
            sim = cosine_similarity(query_embedding, memory['embedding'])
            similarities.append((sim, memory))

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Return top k
        return [mem for sim, mem in similarities[:top_k]]

    def get_all_memories(self) -> List[str]:
        """Get all memory contents"""
        return [m['content'] for m in self.memories]

def demo():
    """Demo the Agent Memory system"""
    print("=" * 60)
    print("Agent Memory Search Demo")
    print("=" * 60)

    # Create an agent and add memories
    agent = AgentMemory("agent_001")

    # Add sample memories
    memories = [
        ("User prefers dark mode interface", {"type": "preference"}),
        ("User's name is John Smith", {"type": "personal_info"}),
        ("User works as a software engineer", {"type": "work_info"}),
        ("User loves coffee in the morning", {"type": "preference"}),
        ("User is working on a Python project", {"type": "project"}),
    ]

    for content, metadata in memories:
        agent.add_memory(content, metadata)
        print(f"Added: {content}")

    print(f"\nTotal memories: {len(agent.get_all_memories())}")
    print("-" * 60)

    # Search queries
    queries = [
        "What does the user like?",
        "Who is the user?",
        "What is the user working on?",
    ]

    for query in queries:
        results = agent.search(query, top_k=2)
        print(f"\nQuery: {query}")
        print(f"Results:")
        for r in results:
            sim = cosine_similarity(simple_embedding(query), r['embedding'])
            print(f"  - {r['content']} (similarity: {sim:.3f})")

if __name__ == "__main__":
    demo()