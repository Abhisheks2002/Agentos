"""
Day 42: Advanced RAG - Hybrid Search & Re-ranking
==================================================
Skill: Advanced RAG Techniques
Mini Project: Enterprise RAG Pipeline

Advanced retrieval techniques including hybrid search,
re-ranking, and context compression.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import json


@dataclass
class Document:
    """Document for retrieval"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: float = 0.0


class BM25:
    """
    BM25 Retrieval - Keyword-based search
    ======================================
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, Document] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length = 0
        self.term_doc_freq: Dict[str, int] = {}
        self.num_docs = 0

    def index(self, documents: List[Document]):
        """Index documents"""
        self.documents = {d.id: d for d in documents}
        self.doc_lengths = [len(d.content.split()) for d in documents]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1
        self.num_docs = len(documents)

        # Calculate term document frequencies
        for doc in documents:
            terms = set(doc.content.lower().split())
            for term in terms:
                self.term_doc_freq[term] = self.term_doc_freq.get(term, 0) + 1

    def search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """Search using BM25"""
        query_terms = query.lower().split()
        scores = {}

        for doc_id, doc in self.documents.items():
            score = 0.0

            for term in query_terms:
                if term in doc.content.lower():
                    # Term frequency
                    tf = doc.content.lower().split().count(term)

                    # IDF
                    df = self.term_doc_freq.get(term, 1)
                    idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)

                    # BM25 formula
                    doc_len = len(doc.content.split())
                    tf_component = (tf * (self.k1 + 1)) / (
                        tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                    )

                    score += idf * tf_component

            if score > 0:
                scores[doc_id] = score

        # Sort by score
        results = [
            (self.documents[doc_id], score)
            for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ]

        return results[:k]


class HybridRetriever:
    """
    Hybrid Retriever - Combine vector + keyword search
    ==================================================
    """

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha  # Weight for vector search
        self.bm25 = BM25()
        self.vector_weight = alpha
        self.keyword_weight = 1 - alpha

    def index(self, documents: List[Document]):
        """Index documents for both searches"""
        self.bm25.index(documents)
        # Store for vector search
        self.documents = {d.id: d for d in documents}

    def search(
        self,
        query: str,
        k: int = 10,
        vector_results: int = 20,
        keyword_results: int = 20
    ) -> List[Document]:
        """Hybrid search combining both methods"""

        # Vector search (simplified)
        vector_results_data = self._vector_search(query, vector_results)

        # Keyword search
        keyword_results_data = self.bm25.search(query, keyword_results)

        # Merge and re-rank
        merged = self._merge_results(vector_results_data, keyword_results_data)

        return merged[:k]

    def _vector_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Simple vector search"""
        # In production: use actual embeddings
        results = []
        for doc in self.documents.values():
            # Simple keyword overlap
            query_terms = set(query.lower().split())
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
            results.append((doc, overlap))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def _merge_results(
        self,
        vector: List[Tuple[Document, float]],
        keyword: List[Tuple[Document, float]]
    ) -> List[Document]:
        """Merge results from both methods"""
        scores = {}

        # Vector scores
        for doc, score in vector:
            scores[doc.id] = scores.get(doc.id, 0) + score * self.vector_weight

        # Keyword scores
        for doc, score in keyword:
            scores[doc.id] = scores.get(doc.id, 0) + score * self.keyword_weight

        # Sort by combined score
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [self.documents[doc_id] for doc_id, _ in sorted_ids]


class ReRanker:
    """
    Re-Ranker - Improve retrieval quality
    =======================================
    """

    def __init__(self, model_name: str = "cross-encoder"):
        self.model_name = model_name

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5
    ) -> List[Document]:
        """Re-rank documents for better relevance"""

        # Score each document
        scored = []
        for doc in documents:
            score = self._score(query, doc)
            doc.score = score
            scored.append((doc, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored[:top_k]]

    def _score(self, query: str, document: Document) -> float:
        """Score query-document pair (simplified)"""
        query_terms = query.lower().split()
        doc_terms = document.content.lower().split()

        # Semantic overlap
        overlap = sum(1 for t in query_terms if t in doc_terms)

        # Position bonus (earlier = better)
        position_score = 1.0
        for i, term in enumerate(doc_terms[:10]):
            if term in query_terms:
                position_score -= i * 0.05

        return overlap + max(0, position_score)


class ContextCompressor:
    """
    Context Compressor - Fit more in context window
    ===============================================
    """

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def compress(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Document]:
        """Compress documents to fit in context"""

        # Sort by relevance
        docs_with_scores = []
        for doc in documents:
            score = self._calc_relevance(query, doc)
            docs_with_scores.append((doc, score))

        docs_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Include as many as fit
        compressed = []
        current_tokens = 0

        for doc, score in docs_with_scores:
            doc_tokens = len(doc.content.split()) * 1.3

            if current_tokens + doc_tokens <= self.max_tokens:
                compressed.append(doc)
                current_tokens += doc_tokens

        return compressed

    def _calc_relevance(self, query: str, document: Document) -> float:
        """Calculate relevance score"""
        query_terms = set(query.lower().split())
        doc_terms = set(document.content.lower().split())

        return len(query_terms & doc_terms) / max(len(query_terms), 1)


class AdvancedRAGPipeline:
    """
    Advanced RAG Pipeline
    ======================

    Complete pipeline with all components
    """

    def __init__(self):
        self.hybrid = HybridRetriever(alpha=0.5)
        self.reranker = ReRanker()
        self.compressor = ContextCompressor()
        self.documents: Dict[str, Document] = {}

    def add_documents(self, documents: List[Document]):
        """Add documents to pipeline"""
        for doc in documents:
            self.documents[doc.id] = doc
        self.hybrid.index(list(self.documents.values()))

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_reranker: bool = True,
        use_compression: bool = True
    ) -> Dict[str, Any]:
        """Retrieve relevant documents"""

        # Initial retrieval (get more than needed for re-ranking)
        initial_k = top_k * 3 if use_reranker else top_k
        results = self.hybrid.search(query, k=initial_k)

        # Re-rank if enabled
        if use_reranker and results:
            results = self.reranker.rerank(query, results, top_k)

        # Compress if enabled
        if use_compression:
            results = self.compressor.compress(query, results)

        return {
            "query": query,
            "documents": [
                {
                    "id": d.id,
                    "content": d.content[:100] + "...",
                    "metadata": d.metadata,
                    "score": d.score
                }
                for d in results[:top_k]
            ],
            "count": len(results)
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Advanced RAG Pipeline Demo")
    print("=" * 70)

    # Sample documents
    docs = [
        Document(
            id="1",
            content="Python is a high-level programming language. It's great for AI and data science.",
            metadata={"source": "doc1", "topic": "python"}
        ),
        Document(
            id="2",
            content="Machine learning is a subset of AI. It uses algorithms to learn from data.",
            metadata={"source": "doc2", "topic": "ml"}
        ),
        Document(
            id="3",
            content="LangChain is a framework for building LLM applications easily.",
            metadata={"source": "doc3", "topic": "langchain"}
        ),
        Document(
            id="4",
            content="Vector databases store embeddings efficiently for similarity search.",
            metadata={"source": "doc4", "topic": "database"}
        ),
        Document(
            id="5",
            content="RAG combines retrieval and generation for better LLM responses.",
            metadata={"source": "doc5", "topic": "rag"}
        ),
    ]

    # Create pipeline
    pipeline = AdvancedRAGPipeline()
    pipeline.add_documents(docs)

    # Retrieve
    print("\n[1] Basic Retrieval")
    print("-" * 40)

    result = pipeline.retrieve("Python programming AI", top_k=3)

    print(f"Query: {result['query']}")
    for doc in result['documents']:
        print(f"  {doc['id']}: {doc['content']}")
        print(f"    Score: {doc['score']:.3f}")

    # Without re-ranking
    print("\n[2] Without Re-ranker")
    print("-" * 40)

    result = pipeline.retrieve("Python", top_k=3, use_reranker=False)
    print(f"Count: {result['count']}")

    # Hybrid search
    print("\n[3] Hybrid Search")
    print("-" * 40)

    hybrid = HybridRetriever(alpha=0.5)
    hybrid.index(docs)
    results = hybrid.search("AI programming", k=3)

    for doc, score in results:
        print(f"  {doc.id}: {doc.content[:50]}... (score: {score:.3f})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()