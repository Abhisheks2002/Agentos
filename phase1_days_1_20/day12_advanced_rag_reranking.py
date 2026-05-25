"""
Day 12: Advanced RAG - Re-ranking & Context Compression
=========================================================
Skill: Making memory more accurate
Mini Project: The Knowledge Specialist

Re-ranking ensures the agent gets the best memory first.
Two-stage retrieval: Search 10 docs, then re-rank to top 3.
"""

from typing import List, Dict, Tuple
import random

class Document:
    """Represents a document for retrieval"""

    def __init__(self, id: str, content: str, metadata: Dict = None):
        self.id = id
        self.content = content
        self.metadata = metadata or {}

class RetrievalResult:
    """Result of a retrieval operation"""

    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score

class SimpleVectorStore:
    """Simple vector store with keyword matching"""

    def __init__(self):
        self.documents: List[Document] = []

    def add(self, doc: Document):
        self.documents.append(doc)

    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """Simple keyword-based initial search"""
        query_words = set(query.lower().split())

        results = []
        for doc in self.documents:
            doc_words = set(doc.content.lower().split())
            # Simple overlap score
            overlap = len(query_words & doc_words)
            if overlap > 0:
                results.append(RetrievalResult(doc, float(overlap)))

        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

class ReRanker:
    """Re-ranks retrieval results for better accuracy"""

    def __init__(self):
        pass

    def rerank(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Re-rank results based on more sophisticated criteria.
        In production, use Cohere or similar for semantic re-ranking.
        """
        # Simple re-ranking logic for demo
        # Consider: position in query, semantic relevance, recency

        reranked = []
        for result in results:
            doc = result.document
            score = result.score

            # Boost score for exact matches
            if query.lower() in doc.content.lower():
                score *= 1.5

            # Boost for certain metadata
            if doc.metadata.get("type") == "official":
                score *= 1.2

            reranked.append(RetrievalResult(doc, score))

        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked

class ContextCompressor:
    """Compresses context to fit in token limit"""

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens

    def compress(self, results: List[RetrievalResult]) -> str:
        """Compress multiple documents into context"""
        context = ""
        total_tokens = 0

        for result in results:
            doc = result.document
            # Rough token estimate: ~4 chars per token
            doc_tokens = len(doc.content) // 4

            if total_tokens + doc_tokens <= self.max_tokens:
                context += f"\n\n--- {doc.id} ---\n{doc.content}"
                total_tokens += doc_tokens
            else:
                break

        return context

class KnowledgeSpecialist:
    """High-accuracy RAG system with re-ranking"""

    def __init__(self):
        self.store = SimpleVectorStore()
        self.reranker = ReRanker()
        self.compressor = ContextCompressor()

    def add_documents(self, docs: List[Dict]):
        """Add documents to knowledge base"""
        for doc in docs:
            self.store.add(Document(
                id=doc["id"],
                content=doc["content"],
                metadata=doc.get("metadata", {})
            ))

    def query(self, question: str) -> Dict:
        """Query with two-stage retrieval and re-ranking"""
        # Stage 1: Initial retrieval (10 docs)
        initial_results = self.store.search(question, top_k=10)

        # Stage 2: Re-rank to top 3
        reranked = self.reranker.rerank(question, initial_results)
        top_results = reranked[:3]

        # Stage 3: Compress context
        context = self.compressor.compress(top_results)

        return {
            "question": question,
            "initial_results": len(initial_results),
            "top_results": len(top_results),
            "context": context,
            "sources": [{"id": r.document.id, "score": r.score} for r in top_results]
        }

def demo():
    """Demo The Knowledge Specialist"""
    print("=" * 70)
    print("The Knowledge Specialist - Advanced RAG Demo")
    print("=" * 70)

    specialist = KnowledgeSpecialist()

    # Add documents about AgentOS
    docs = [
        {
            "id": "doc_001",
            "content": "AgentOS installation: Run pip install agentos-sdk. Configure API keys in .env file. Initialize with agentos init command.",
            "metadata": {"type": "official", "topic": "installation"}
        },
        {
            "id": "doc_002",
            "content": "Agent permissions: Admin agents have full access. User agents can read and write. Guest agents can only read. Permissions are defined in agentos.json.",
            "metadata": {"type": "official", "topic": "permissions"}
        },
        {
            "id": "doc_003",
            "content": "The weather today is sunny with a high of 75 degrees.",
            "metadata": {"type": "external", "topic": "weather"}
        },
        {
            "id": "doc_004",
            "content": "Memory system: Use memory.save(key, value) to store memories. Use memory.search(query) to retrieve. Memories persist across sessions.",
            "metadata": {"type": "official", "topic": "memory"}
        },
        {
            "id": "doc_005",
            "content": "Tool registration: Use @tool decorator to register new tools. Define name, description, and parameters in the decorator.",
            "metadata": {"type": "official", "topic": "tools"}
        },
        {
            "id": "doc_006",
            "content": "Python is a programming language. It's great for AI and data science. Python was created by Guido van Rossum.",
            "metadata": {"type": "general", "topic": "python"}
        },
    ]

    specialist.add_documents(docs)

    # Test queries
    queries = [
        "How do I install AgentOS?",
        "What are agent permissions?",
        "How do I save memories?",
    ]

    for query in queries:
        result = specialist.query(query)
        print(f"\nQuery: {query}")
        print("-" * 50)
        print(f"Retrieved {result['initial_results']} → Re-ranked to {result['top_results']}")
        print(f"Sources: {[s['id'] for s in result['sources']]}")
        print(f"Context preview: {result['context'][:150]}...")

if __name__ == "__main__":
    demo()