"""
Day 6: RAG (Retrieval Augmented Generation)
============================================
Skill: Basic RAG Pipelines
Mini Project: Agent Manual Bot

RAG lets agents look up info before answering.
Query -> Vector Search -> Context -> LLM Answer
"""

import os
from typing import List, Dict, Optional
from pydantic import BaseModel

# Simulated vector store (in production, use Pinecone, Weaviate, etc.)
class SimpleVectorStore:
    """Simple in-memory vector store for demo"""

    def __init__(self):
        self.documents = []
        self.doc_embeddings = []

    def add_documents(self, docs: List[Dict[str, str]]):
        """Add documents to the store"""
        for doc in docs:
            self.documents.append({
                "id": doc.get("id", f"doc_{len(self.documents)}"),
                "content": doc["content"],
                "metadata": doc.get("metadata", {})
            })

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Simple keyword-based search (in production, use vector similarity)"""
        query_lower = query.lower()
        results = []

        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Simple scoring based on keyword matching
            score = sum(1 for word in query_lower.split() if word in content_lower)
            if score > 0:
                results.append({
                    "id": doc["id"],
                    "content": doc["content"],
                    "score": score,
                    "metadata": doc["metadata"]
                })

        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

class AgentManualBot:
    """Agent that answers questions based on provided documentation"""

    def __init__(self, documentation: List[Dict[str, str]]):
        self.vector_store = SimpleVectorStore()
        self.vector_store.add_documents(documentation)
        self.system_prompt = """You are AgentOS Help Bot. You MUST only answer
based on the provided documentation. If the answer is not in the docs,
say "I don't have that information in my knowledge base." """

    def retrieve_context(self, query: str) -> str:
        """Retrieve relevant context for the query"""
        results = self.vector_store.search(query, top_k=3)
        if not results:
            return ""

        context = "RELEVANT DOCUMENTATION:\n\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. {result['content']}\n\n"
        return context

    def generate_answer(self, query: str) -> str:
        """Generate answer using RAG pattern"""
        context = self.retrieve_context(query)

        if not context:
            return "I don't have that information in my knowledge base."

        # In production, use OpenAI with the context
        # For demo, we'll return a simulated response
        return f"Based on the documentation:\n{context[:200]}...\n\n[In production, this would call the LLM with the context]"

# AgentOS Documentation
AGENT_OS_DOCS = [
    {
        "id": "doc_001",
        "content": "AgentOS Quick Start Guide: To install AgentOS, run 'pip install agentos-sdk'. Then initialize with 'agentos init'. Configure your API keys in .env file.",
        "metadata": {"section": "getting-started", "topic": "installation"}
    },
    {
        "id": "doc_002",
        "content": "Agent Configuration: Edit agentos.json to configure agent behavior. Set max_tokens, temperature, and system_prompt. Agents can have roles: admin, user, or guest.",
        "metadata": {"section": "configuration", "topic": "agents"}
    },
    {
        "id": "doc_003",
        "content": "Memory System: AgentOS uses vector storage for agent memory. Use memory.save() to store memories and memory.search() to retrieve. Memories are agent-specific by default.",
        "metadata": {"section": "features", "topic": "memory"}
    },
    {
        "id": "doc_004",
        "content": "Tool Registration: Register tools using @tool decorator. Tools must define name, description, and parameters schema. Tools are scoped by agent permission level.",
        "metadata": {"section": "development", "topic": "tools"}
    },
    {
        "id": "doc_005",
        "content": "Security: AgentOS implements RBAC (Role-Based Access Control). Admin agents can access all tools. Guest agents can only read. All actions are logged for audit.",
        "metadata": {"section": "security", "topic": "rbac"}
    },
]

def demo():
    """Demo the Agent Manual Bot"""
    print("=" * 70)
    print("Agent Manual Bot - RAG Demo")
    print("=" * 70)

    # Create the bot with documentation
    bot = AgentManualBot(AGENT_OS_DOCS)

    # Test questions
    questions = [
        "How do I install AgentOS?",
        "What are the agent roles?",
        "How does memory work?",
        "What is the weather like today?",  # Not in docs
    ]

    for question in questions:
        print(f"\nQ: {question}")
        print("-" * 50)
        answer = bot.generate_answer(question)
        print(f"A: {answer}")
        print()

if __name__ == "__main__":
    demo()