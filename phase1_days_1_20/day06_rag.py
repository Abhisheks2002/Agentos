"""
Day 6: RAG (Retrieval Augmented Generation)
=============================================
Skill: Basic RAG Pipelines
Mini Project: Agent Manual Bot

An agent that can only answer questions based on a provided AgentOS_Documentation.pdf.
Builds a simple retrieval loop: Query -> Vector Search -> Context -> LLM Answer.
"""

import os
import json
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

# Simple vector store for demo (in production, use Pinecone, Weaviate, etc.)
class SimpleVectorStore:
    """Simple in-memory vector store for RAG"""

    def __init__(self):
        self.documents = []
        self.embeddings = []

    def add_documents(self, docs: List[Dict]):
        """Add documents with their embeddings"""
        for doc in docs:
            # Simple hash-based embedding
            embedding = self._simple_embed(doc['content'])
            self.documents.append(doc)
            self.embeddings.append(embedding)

    def _simple_embed(self, text: str) -> np.ndarray:
        """Simple text embedding"""
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(5).astype(np.float32)

    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar documents"""
        query_embedding = self._simple_embed(query)

        # Calculate similarities
        scores = []
        for i, emb in enumerate(self.embeddings):
            sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-8)
            scores.append((i, sim))

        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for i, score in scores[:top_k]:
            results.append({
                **self.documents[i],
                'score': float(score)
            })

        return results

class AgentManualBot:
    """RAG-based bot that answers from AgentOS documentation"""

    def __init__(self):
        self.vector_store = SimpleVectorStore()
        self._load_documentation()

    def _load_documentation(self):
        """Load AgentOS documentation"""
        docs = [
            {
                "id": "doc_001",
                "title": "AgentOS Overview",
                "content": "AgentOS is an AI Agent Governance Platform. It provides enterprise governance, agent management, workflow automation, and OS bridge capabilities."
            },
            {
                "id": "doc_002",
                "title": "Installation",
                "content": "To install AgentOS, run 'npm install' then 'npm start'. Prerequisites: Node.js 18+, Python 3.8+."
            },
            {
                "id": "doc_003",
                "title": "API Endpoints",
                "content": "AgentOS provides REST API endpoints: /api/agents for agent management, /api/workflows for workflow automation, /api/files for file operations."
            },
            {
                "id": "doc_004",
                "title": "Security",
                "content": "AgentOS implements role-based access control (RBAC). Actions like system file deletion and registry modification are auto-blocked."
            },
            {
                "id": "doc_005",
                "title": "Agent Types",
                "content": "AgentOS supports three organization tiers: Startup (5 agents, 10 workflows), Business (25 agents, 100 workflows), Enterprise (unlimited)."
            },
            {
                "id": "doc_006",
                "title": "Memory System",
                "content": "Agents have persistent memory using vector databases. They can remember user preferences, past interactions, and context."
            }
        ]
        self.vector_store.add_documents(docs)

    def query(self, question: str) -> Dict:
        """Answer a question using RAG"""
        # Step 1: Retrieve relevant documents
        relevant_docs = self.vector_store.similarity_search(question, top_k=3)

        # Step 2: Build context from retrieved docs
        context = "\n\n".join([doc['content'] for doc in relevant_docs])

        # Step 3: Generate answer (simulated - in production, use LLM)
        answer = self._generate_answer(question, context, relevant_docs)

        return {
            "question": question,
            "answer": answer,
            "sources": [doc['title'] for doc in relevant_docs],
            "retrieved_docs": relevant_docs
        }

    def _generate_answer(self, question: str, context: str, sources: List[Dict]) -> str:
        """Generate answer from context (simulated LLM)"""
        # Simple keyword-based response (in production, use GPT-4)
        question_lower = question.lower()

        if "install" in question_lower or "setup" in question_lower:
            return "To install AgentOS, run 'npm install' then 'npm start'. Prerequisites: Node.js 18+ and Python 3.8+."
        elif "api" in question_lower or "endpoint" in question_lower:
            return "AgentOS API endpoints include: /api/agents for agent management, /api/workflows for workflows, and /api/files for file operations."
        elif "tier" in question_lower or "limit" in question_lower:
            return "AgentOS has three tiers: Startup (5 agents, 10 workflows), Business (25 agents, 100 workflows), Enterprise (unlimited)."
        elif "security" in question_lower or "permission" in question_lower:
            return "AgentOS uses RBAC for security. System file deletion and registry modifications are auto-blocked."
        else:
            return f"Based on the AgentOS documentation: {context[:200]}..."

def demo():
    """Demo the Agent Manual Bot"""
    print("=" * 70)
    print("Agent Manual Bot - RAG Demo")
    print("=" * 70)

    bot = AgentManualBot()

    questions = [
        "How do I install AgentOS?",
        "What are the API endpoints?",
        "What are the different pricing tiers?",
        "How does security work?",
    ]

    for question in questions:
        result = bot.query(question)
        print(f"\nQ: {result['question']}")
        print(f"A: {result['answer']}")
        print(f"Sources: {', '.join(result['sources'])}")

if __name__ == "__main__":
    demo()