"""Query Processor for Agentic RAG - Day 10 Implementation.

This module handles query understanding, decomposition, and intent classification.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intents."""
    FACTUAL = "factual"
    EXPLANATORY = "explanatory"
    COMPARATIVE = "comparative"
    PROCEDURAL = "procedural"
    ANALYTICAL = "analytical"
    SUMMARY = "summary"
    DIRECTED = "directed"  # Specific topic search
    AMBIGUOUS = "ambiguous"


@dataclass
class QueryAnalysis:
    """Result of query analysis."""
    original_query: str
    intent: QueryIntent
    decomposed_queries: List[str]
    keywords: List[str]
    entities: List[str]
    constraints: Dict[str, Any]
    confidence: float


@dataclass
class SearchResult:
    """Represents a retrieved search result."""
    chunk_id: str
    content: str
    document_id: str
    score: float
    metadata: Dict[str, Any]


class QueryProcessor:
    """Process and analyze queries for Agentic RAG."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._setup_patterns()

    def _setup_patterns(self):
        """Setup regex patterns for query analysis."""
        # Entity patterns for common entity types
        self.entity_patterns = {
            'date': r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4}|january|february|march|april|may|june|july|august|september|october|november|december)\b',
            'number': r'\b\d+(?:\.\d+)?\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://[^\s]+',
        }

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a query and return structured analysis."""
        if not query or not query.strip():
            return QueryAnalysis(
                original_query=query,
                intent=QueryIntent.AMBIGUOUS,
                decomposed_queries=[],
                keywords=[],
                entities=[],
                constraints={},
                confidence=0.0
            )

        # Extract components
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        intent = self._classify_intent(query)
        decomposed = self._decompose_query(query, intent)
        constraints = self._extract_constraints(query)

        # Calculate confidence based on analysis completeness
        confidence = self._calculate_confidence(query, keywords, entities, intent)

        return QueryAnalysis(
            original_query=query,
            intent=intent,
            decomposed_queries=decomposed,
            keywords=keywords,
            entities=entities,
            constraints=constraints,
            confidence=confidence
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Remove stopwords
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'also', 'now', 'what', 'which',
            'who', 'whom', 'this', 'that', 'these', 'those'
        }

        words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        keywords = [w for w in words if w not in stopwords]
        return list(set(keywords))

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query."""
        entities = []
        query_lower = query.lower()

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)

        return list(set(entities))

    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query."""
        query_lower = query.lower()

        # Check for comparative queries
        if any(word in query_lower for word in ['compare', 'difference', 'vs', 'versus', 'better', 'worse']):
            return QueryIntent.COMPARATIVE

        # Check for procedural/how-to queries
        if any(word in query_lower for word in ['how to', 'how do', 'how can', 'steps', 'process', 'procedure', 'guide']):
            return QueryIntent.PROCEDURAL

        # Check for explanatory queries
        if any(word in query_lower for word in ['why', 'reason', 'explain', 'meaning', 'what is', 'what are', 'define']):
            return QueryIntent.EXPLANATORY

        # Check for analytical queries
        if any(word in query_lower for word in ['analyze', 'impact', 'effect', 'benefit', 'advantage', 'disadvantage', 'pros', 'cons']):
            return QueryIntent.ANALYTICAL

        # Check for summary requests
        if any(word in query_lower for word in ['summarize', 'summary', 'overview', 'brief', 'concise']):
            return QueryIntent.SUMMARY

        # Check for directed/topic queries
        if any(word in query_lower for word in ['about', 'regarding', 'concerning', 'related to', 'information on']):
            return QueryIntent.DIRECTED

        # Check for factual queries (who, what, when, where)
        if any(word in query_lower for word in ['who', 'what', 'when', 'where']):
            return QueryIntent.FACTUAL

        # Default to directed search
        return QueryIntent.DIRECTED

    def _decompose_query(self, query: str, intent: QueryIntent) -> List[str]:
        """Decompose complex query into sub-queries."""
        queries = [query]

        # For comparative queries, create separate queries for each side
        if intent == QueryIntent.COMPARATIVE:
            # Look for "X vs Y" patterns
            vs_match = re.search(r'(.+?)\s+(?:vs|versus|or)\s+(.+)', query, re.IGNORECASE)
            if vs_match:
                queries = [
                    vs_match.group(1).strip(),
                    vs_match.group(2).strip()
                ]

        # For multi-part queries (separated by "and", "or", ";")
        elif any(connector in query.lower() for connector in [' and ', ';', ' also ']):
            # Split by common connectors
            parts = re.split(r'\s+and\s+|\s*;\s*|\s+also\s+', query)
            if len(parts) > 1:
                queries = [p.strip() for p in parts if p.strip()]

        # For questions with multiple aspects
        if intent in [QueryIntent.EXPLANATORY, QueryIntent.ANALYTICAL]:
            # Extract sub-questions starting with what, why, how
            sub_patterns = [
                r'(what[\w\s]+)',
                r'(why[\w\s]+)',
                r'(how[\w\s]+)',
                r'(when[\w\s]+)'
            ]
            sub_queries = []
            for pattern in sub_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                sub_queries.extend(matches)

            if sub_queries:
                # Keep original as first, add sub-queries
                queries = [query] + sub_queries[:3]  # Limit to 3 sub-queries

        return queries

    def _extract_constraints(self, query: str) -> Dict[str, Any]:
        """Extract constraints from query."""
        constraints = {}
        query_lower = query.lower()

        # Time constraints
        if 'recent' in query_lower or 'latest' in query_lower:
            constraints['time_range'] = 'recent'
        if 'old' in query_lower or 'historical' in query_lower:
            constraints['time_range'] = 'historical'

        # Scope constraints
        if 'brief' in query_lower or 'short' in query_lower:
            constraints['response_length'] = 'short'
        elif 'detailed' in query_lower or 'comprehensive' in query_lower:
            constraints['response_length'] = 'long'
        elif 'concise' in query_lower:
            constraints['response_length'] = 'concise'

        # Source constraints
        if 'according to' in query_lower or 'source' in query_lower:
            constraints['source_attribution'] = True

        # Format constraints
        if 'list' in query_lower:
            constraints['format'] = 'list'
        if 'step' in query_lower:
            constraints['format'] = 'steps'

        return constraints

    def _calculate_confidence(self, query: str, keywords: List[str], entities: List[str], intent: QueryIntent) -> float:
        """Calculate confidence score for the analysis."""
        confidence = 0.5  # Base confidence

        # More keywords = higher confidence
        if len(keywords) >= 3:
            confidence += 0.15
        elif len(keywords) >= 1:
            confidence += 0.1

        # Entities found = higher confidence
        if entities:
            confidence += 0.15

        # Non-ambiguous intent = higher confidence
        if intent != QueryIntent.AMBIGUOUS:
            confidence += 0.2

        return min(confidence, 1.0)


class MultiSourceRetriever:
    """Retrieve documents from multiple sources."""

    def __init__(self):
        self.sources = {}

    def add_source(self, name: str, retriever_func, weights: float = 1.0):
        """Add a retrieval source."""
        self.sources[name] = {
            'retriever': retriever_func,
            'weights': weights
        }

    async def retrieve(self, query: str, query_analysis: QueryAnalysis, top_k: int = 10) -> List[SearchResult]:
        """Retrieve from all sources and merge results."""
        all_results = []

        # Run all retrievers in parallel
        for source_name, source_config in self.sources.items():
            try:
                retriever = source_config['retriever']
                weights = source_config['weights']

                # Call the retriever function
                if callable(retriever):
                    results = await self._call_retriever(retriever, query, query_analysis, top_k)

                    # Apply weights to scores
                    for result in results:
                        result.score *= weights

                    all_results.extend(results)

            except Exception as e:
                logger.error(f"Error retrieving from source {source_name}: {e}")

        # Sort by score and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    async def _call_retriever(self, retriever, query: str, query_analysis: QueryAnalysis, top_k: int):
        """Call a retriever function (handles both sync and async)."""
        import asyncio

        if asyncio.iscoroutinefunction(retriever):
            return await retriever(query, query_analysis, top_k)
        else:
            return retriever(query, query_analysis, top_k)


class Reranker:
    """Re-rank search results for better relevance."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """Re-rank results based on relevance to query."""
        if not results:
            return []

        # If LLM client available, use it for semantic reranking
        if self.llm_client:
            return self._llm_rerank(query, results, top_k)

        # Otherwise use keyword-based reranking
        return self._keyword_rerank(query, results, top_k)

    def _keyword_rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Rerank using keyword overlap."""
        query_keywords = set(query.lower().split())

        for result in results:
            # Calculate keyword overlap score
            content_words = set(result.content.lower().split())
            overlap = len(query_keywords & content_words)
            keyword_score = overlap / max(len(query_keywords), 1)

            # Combine with original score (50/50 weight)
            result.score = (result.score * 0.5) + (keyword_score * 0.5)

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _llm_rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Rerank using LLM for semantic relevance."""
        # For now, fallback to keyword reranking
        # In production, this would use LLM-based scoring
        return self._keyword_rerank(query, results, top_k)


class ResponseSynthesizer:
    """Synthesize final response from retrieved chunks."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def synthesize(
        self,
        query: str,
        query_analysis: QueryAnalysis,
        results: List[SearchResult]
    ) -> Dict[str, Any]:
        """Synthesize response from retrieved results."""
        if not results:
            return {
                'response': 'No relevant information found.',
                'sources': [],
                'confidence': 0.0
            }

        # Organize results by document
        source_docs = {}
        for result in results:
            doc_id = result.document_id
            if doc_id not in source_docs:
                source_docs[doc_id] = {
                    'metadata': result.metadata,
                    'chunks': []
                }
            source_docs[doc_id]['chunks'].append({
                'content': result.content,
                'score': result.score
            })

        # Generate response
        if self.llm_client and query_analysis.confidence > 0.5:
            response = await self._llm_synthesize(query, query_analysis, source_docs)
        else:
            response = self._template_synthesize(query, query_analysis, source_docs)

        # Extract source information
        sources = [
            {
                'document_id': doc_id,
                'metadata': info['metadata'],
                'relevant_chunks': len(info['chunks'])
            }
            for doc_id, info in source_docs.items()
        ]

        # Calculate overall confidence
        avg_score = sum(r.score for r in results) / len(results)
        confidence = min(avg_score * query_analysis.confidence, 1.0)

        return {
            'response': response,
            'sources': sources,
            'confidence': confidence,
            'query_intent': query_analysis.intent.value
        }

    async def _llm_synthesize(
        self,
        query: str,
        query_analysis: QueryAnalysis,
        source_docs: Dict
    ) -> str:
        """Generate response using LLM."""
        # Build context from chunks
        context_parts = []
        for doc_id, info in source_docs.items():
            for chunk in info['chunks'][:3]:  # Top 3 chunks per doc
                context_parts.append(chunk['content'])

        context = "\n\n".join(context_parts)

        # Build prompt based on intent
        prompt = self._build_prompt(query, query_analysis, context)

        try:
            # Call LLM (placeholder - would integrate with actual LLM)
            # response = await self.llm_client.complete(prompt)
            # return response

            # Fallback to template synthesis
            return self._template_synthesize(query, query_analysis, source_docs)
        except Exception as e:
            logger.error(f"LLM synthesis error: {e}")
            return self._template_synthesize(query, query_analysis, source_docs)

    def _build_prompt(self, query: str, query_analysis: QueryAnalysis, context: str) -> str:
        """Build prompt for LLM synthesis."""
        intent = query_analysis.intent.value

        prompt = f"""Based on the following context, answer the question.
If the context doesn't contain relevant information, say so.

Question: {query}
Query Type: {intent}

Context:
{context}

Answer:"""

        return prompt

    def _template_synthesize(
        self,
        query: str,
        query_analysis: QueryAnalysis,
        source_docs: Dict
    ) -> str:
        """Template-based response synthesis."""
        intent = query_analysis.intent

        # Collect all relevant content
        all_content = []
        for doc_id, info in source_docs.items():
            for chunk in info['chunks']:
                all_content.append(chunk['content'])

        if intent == QueryIntent.SUMMARY:
            # Return concise summary
            return self._generate_summary(all_content)
        elif intent == QueryIntent.COMPARATIVE:
            return self._generate_comparison(all_content)
        elif intent == QueryIntent.PROCEDURAL:
            return self._generate_procedure(all_content)
        else:
            # Default: combine relevant information
            return self._generate_default(all_content, query)

    def _generate_summary(self, contents: List[str]) -> str:
        """Generate summary from contents."""
        combined = "\n".join(contents[:5])  # Use top 5 chunks
        return f"Based on the available information:\n\n{combined[:500]}..."

    def _generate_comparison(self, contents: List[str]) -> str:
        """Generate comparison response."""
        return "Based on the retrieved information, here are the key points:\n\n" + "\n".join(contents[:4])

    def _generate_procedure(self, contents: List[str]) -> str:
        """Generate procedural response."""
        return "Here are the relevant steps and information:\n\n" + "\n".join(contents[:4])

    def _generate_default(self, contents: List[str], query: str) -> str:
        """Generate default response."""
        return "Based on the retrieved information:\n\n" + "\n\n".join(contents[:3])


class AgenticRAG:
    """Main Agentic RAG pipeline."""

    def __init__(
        self,
        llm_client=None,
        vector_store=None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.query_processor = QueryProcessor(llm_client)
        self.retriever = MultiSourceRetriever()
        self.reranker = Reranker(llm_client)
        self.synthesizer = ResponseSynthesizer(llm_client)
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def add_vector_source(self, name: str, retriever_func, weights: float = 1.0):
        """Add a vector store as a retrieval source."""
        self.retriever.add_source(name, retriever_func, weights)

    async def query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Process a query through the full RAG pipeline."""
        # Step 1: Analyze query
        query_analysis = self.query_processor.analyze(query)
        logger.info(f"Query intent: {query_analysis.intent.value}, confidence: {query_analysis.confidence:.2f}")

        # Step 2: Retrieve from multiple sources
        raw_results = await self.retriever.retrieve(query, query_analysis, top_k * 2)

        if not raw_results:
            return {
                'response': 'No relevant information found.',
                'sources': [],
                'confidence': 0.0,
                'query_intent': query_analysis.intent.value
            }

        # Step 3: Re-rank results
        reranked_results = self.reranker.rerank(query, raw_results, top_k)

        # Step 4: Synthesize response
        result = await self.synthesizer.synthesize(query, query_analysis, reranked_results)

        return result