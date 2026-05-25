"""Agentic RAG Query Engine - Day 10 Implementation.

This module handles query understanding, decomposition, multi-source retrieval,
re-ranking, and synthesis for Agentic RAG.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent types for understanding user queries."""
    FACTUAL = "factual"
    COMPARISON = "comparison"
    EXPLANATION = "explanation"
    INSTRUCTION = "instruction"
    LIST = "list"
    SUMMARY = "summary"
    COMPLEX = "complex"


@dataclass
class QueryDecomposition:
    """Represents a decomposed query."""
    original_query: str
    sub_queries: List[str]
    intent: QueryIntent
    requires_multi_source: bool
    keywords: List[str] = field(default_factory=list)


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with relevance score."""
    id: str
    content: str
    document_id: str
    metadata: Dict[str, Any]
    score: float
    source: str = ""


@dataclass
class RAGResponse:
    """Final RAG response with sources."""
    answer: str
    sources: List[RetrievedChunk]
    query_decomposition: Optional[QueryDecomposition] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryAnalyzer(ABC):
    """Base class for query analyzers."""

    @abstractmethod
    def analyze(self, query: str) -> QueryDecomposition:
        """Analyze a query and return decomposition."""
        pass


class SimpleQueryAnalyzer(QueryAnalyzer):
    """Simple rule-based query analyzer."""

    def analyze(self, query: str) -> QueryDecomposition:
        """Analyze query using rules."""
        # Extract keywords
        keywords = self._extract_keywords(query)

        # Determine intent
        intent = self._determine_intent(query)

        # Check if multi-source needed
        requires_multi_source = self._requires_multiple_sources(query)

        # Decompose query if complex
        sub_queries = self._decompose_query(query)

        return QueryDecomposition(
            original_query=query,
            sub_queries=sub_queries,
            intent=intent,
            requires_multi_source=requires_multi_source,
            keywords=keywords
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these',
            'those', 'am', 'is', 'are', 'was', 'were', 'being', 'been'
        }

        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))

    def _determine_intent(self, query: str) -> QueryIntent:
        """Determine query intent."""
        query_lower = query.lower()

        # Check for comparison
        if any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs', 'better', 'worse']):
            return QueryIntent.COMPARISON

        # Check for list request
        if any(word in query_lower for word in ['list', 'enumerate', 'what are', 'name']):
            return QueryIntent.LIST

        # Check for explanation
        if any(word in query_lower for word in ['why', 'how does', 'explain', 'meaning', 'what is']):
            return QueryIntent.EXPLANATION

        # Check for instruction
        if any(word in query_lower for word in ['how to', 'how do', 'steps', 'guide', 'tutorial']):
            return QueryIntent.INSTRUCTION

        # Check for summary
        if any(word in query_lower for word in ['summarize', 'summary', 'overview', 'brief']):
            return QueryIntent.SUMMARY

        # Check for complex query
        if query.count('?') > 1 or len(query.split()) > 20:
            return QueryIntent.COMPLEX

        return QueryIntent.FACTUAL

    def _requires_multiple_sources(self, query: str) -> bool:
        """Check if query requires multiple sources."""
        query_lower = query.lower()

        multi_indicators = [
            'compare', 'different', 'various', 'multiple', 'several',
            'both', 'all', 'various', 'multiple sources'
        ]

        return any(indicator in query_lower for indicator in multi_indicators)

    def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-queries."""
        # Check for conjunctions that suggest decomposition
        decomposition_markers = [' and ', ' or ', ' also ', ' plus ', ', also ']

        for marker in decomposition_markers:
            if marker in query.lower():
                parts = query.split(marker)
                if len(parts) > 1:
                    return [p.strip() for p in parts if p.strip()]

        return [query]


class BaseRetriever(ABC):
    """Base class for retrievers."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks for a query."""
        pass


class InMemoryRetriever(BaseRetriever):
    """Simple in-memory retriever using keyword matching.

    In production, this would be replaced with vector embeddings + similarity search.
    """

    def __init__(self):
        self.chunks: List[RetrievedChunk] = []
        self.chunk_texts: Dict[str, str] = {}

    def add_chunks(self, chunks: List[RetrievedChunk]):
        """Add chunks to the retriever."""
        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_texts[chunk.id] = chunk.content

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks using keyword matching."""
        if not self.chunks:
            return []

        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))

        # Score chunks by keyword overlap
        scored_chunks = []
        for chunk in self.chunks:
            # Apply filters if provided
            if filters:
                chunk_matches = True
                for key, value in filters.items():
                    if chunk.metadata.get(key) != value:
                        chunk_matches = False
                        break
                if not chunk_matches:
                    continue

            # Calculate keyword overlap score
            chunk_keywords = set(re.findall(r'\b\w+\b', chunk.content.lower()))
            overlap = query_keywords.intersection(chunk_keywords)
            score = len(overlap) / max(len(query_keywords), 1)

            scored_chunks.append((score, chunk))

        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k]]


class Reranker(ABC):
    """Base class for rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """Rerank chunks based on relevance."""
        pass


class KeywordReranker(Reranker):
    """Simple keyword-based reranker."""

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """Rerank using keyword matching."""
        if not chunks:
            return []

        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))

        reranked = []
        for chunk in chunks:
            chunk_keywords = set(re.findall(r'\b\w+\b', chunk.content.lower()))

            # Calculate multiple scores
            exact_match = len(query_keywords.intersection(chunk_keywords))
            partial_match = sum(1 for qk in query_keywords if any(qk in ck for ck in chunk_keywords))

            # Boost for exact matches in title/source
            title_boost = 0
            if chunk.metadata.get('title'):
                title = chunk.metadata['title'].lower()
                if any(qk in title for qk in query_keywords):
                    title_boost = 0.3

            # Calculate final score
            final_score = (
                chunk.score * 0.4 +
                (exact_match / max(len(query_keywords), 1)) * 0.3 +
                (partial_match / max(len(chunk_keywords), 1)) * 0.3 +
                title_boost
            )

            # Create new chunk with updated score
            new_chunk = RetrievedChunk(
                id=chunk.id,
                content=chunk.content,
                document_id=chunk.document_id,
                metadata=chunk.metadata,
                score=final_score,
                source=chunk.source
            )
            reranked.append((final_score, new_chunk))

        # Sort by final score
        reranked.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in reranked[:top_k]]


class Synthesizer(ABC):
    """Base class for response synthesizers."""

    @abstractmethod
    def synthesize(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        query_decomposition: Optional[QueryDecomposition] = None
    ) -> RAGResponse:
        """Synthesize a response from retrieved chunks."""
        pass


class SimpleSynthesizer(Synthesizer):
    """Simple synthesis by extracting relevant information."""

    def synthesize(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        query_decomposition: Optional[QueryDecomposition] = None
    ) -> RAGResponse:
        """Synthesize response from chunks."""
        if not chunks:
            return RAGResponse(
                answer="I couldn't find relevant information to answer your query.",
                sources=[],
                confidence=0.0
            )

        # Combine content from top chunks
        combined_content = "\n\n".join([
            chunk.content for chunk in chunks[:3]
        ])

        # Simple answer generation
        answer = self._generate_answer(query, combined_content, chunks)

        # Calculate confidence based on scores
        confidence = sum(chunk.score for chunk in chunks) / len(chunks) if chunks else 0.0

        return RAGResponse(
            answer=answer,
            sources=chunks,
            query_decomposition=query_decomposition,
            confidence=confidence,
            metadata={
                "chunks_used": len(chunks),
                "total_chunks_available": len(chunks)
            }
        )

    def _generate_answer(
        self,
        query: str,
        combined_content: str,
        chunks: List[RetrievedChunk]
    ) -> str:
        """Generate a simple answer from content."""
        # In production, this would use an LLM for synthesis
        # For now, we'll create a simple extraction-based answer

        # Get the most relevant chunk
        top_chunk = chunks[0] if chunks else None

        if not top_chunk:
            return "I found some relevant information but couldn't generate a response."

        # Extract a relevant portion
        content = top_chunk.content

        # Truncate if too long
        max_length = 500
        if len(content) > max_length:
            # Find a good break point
            break_point = content[:max_length].rfind('. ')
            if break_point > max_length // 2:
                content = content[:break_point + 1]
            else:
                content = content[:max_length] + "..."

        # Format answer based on query type
        query_lower = query.lower()

        if any(word in query_lower for word in ['what is', 'what are', 'define']):
            return f"Based on the information: {content}"

        if any(word in query_lower for word in ['how to', 'steps', 'guide']):
            return f"Here are the relevant steps: {content}"

        if any(word in query_lower for word in ['compare', 'difference']):
            return f"Here's a comparison based on the sources:\n{content}"

        return f"Here's what I found: {content}"


class AgenticRAG:
    """Main Agentic RAG system that orchestrates all components."""

    def __init__(
        self,
        analyzer: Optional[QueryAnalyzer] = None,
        retriever: Optional[BaseRetriever] = None,
        reranker: Optional[Reranker] = None,
        synthesizer: Optional[Synthesizer] = None
    ):
        self.analyzer = analyzer or SimpleQueryAnalyzer()
        self.retriever = retriever or InMemoryRetriever()
        self.reranker = reranker or KeywordReranker()
        self.synthesizer = synthesizer or SimpleSynthesizer()

    def add_documents(self, documents: List[Any], chunk_size: int = 1000):
        """Add documents to the RAG system."""
        from core.rag.document_loader import DocumentLoaderFactory
        from core.rag.text_chunker import DocumentChunker

        # Load documents
        loaded_docs = []
        for doc in documents:
            if hasattr(doc, 'content'):
                loaded_docs.append(doc)
            else:
                # Assume it's a file path
                loaded = DocumentLoaderFactory.load(doc)
                loaded_docs.extend(loaded)

        # Chunk documents
        chunker = DocumentChunker(chunk_size=chunk_size)
        chunks = chunker.chunk_documents(loaded_docs)

        # Convert to RetrievedChunk
        retrieved_chunks = []
        for chunk in chunks:
            retrieved = RetrievedChunk(
                id=chunk.id,
                content=chunk.content,
                document_id=chunk.document_id,
                metadata=chunk.metadata,
                score=0.0,
                source=chunk.metadata.get('source', '')
            )
            retrieved_chunks.append(retrieved)

        # Add to retriever
        self.retriever.add_chunks(retrieved_chunks)

    def query(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """Process a query through the full RAG pipeline."""
        logger.info(f"Processing query: {query}")

        # Step 1: Analyze query
        query_decomposition = self.analyzer.analyze(query)
        logger.info(f"Query intent: {query_decomposition.intent.value}")

        # Step 2: Retrieve chunks
        retrieved_chunks = self.retriever.retrieve(
            query,
            top_k=top_k * 2 if rerank else top_k,  # Get more for reranking
            filters=filters
        )
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks")

        # Step 3: Rerank if enabled
        if rerank and retrieved_chunks:
            retrieved_chunks = self.reranker.rerank(query, retrieved_chunks, top_k)
            logger.info(f"Reranked to top {len(retrieved_chunks)} chunks")

        # Step 4: Synthesize response
        response = self.synthesizer.synthesize(
            query,
            retrieved_chunks,
            query_decomposition
        )

        logger.info(f"Generated response with confidence: {response.confidence:.2f}")
        return response

    def query_with_sources(
        self,
        query: str,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Query and return answer with source citations."""
        response = self.query(query, top_k=top_k)

        sources = []
        for chunk in response.sources:
            sources.append({
                'id': chunk.id,
                'content': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content,
                'source': chunk.source,
                'score': chunk.score
            })

        return response.answer, sources