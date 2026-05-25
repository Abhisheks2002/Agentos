"""Text Chunker for Agentic RAG - Day 10 Implementation.

This module handles splitting documents into smaller chunks for embedding.
"""

import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with its metadata."""
    id: str
    content: str
    document_id: str
    metadata: Dict[str, Any]
    start_index: int = 0
    end_index: int = 0


class BaseChunker(ABC):
    """Base class for text chunkers."""

    @abstractmethod
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text into chunks."""
        pass


class RecursiveChunker(BaseChunker):
    """Split text using recursive character splitting.

    This is the recommended chunker as it tries to keep related text together.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text into chunks using recursive approach."""
        if not text:
            return []

        metadata = metadata or {}
        chunks = []
        doc_id = metadata.get("document_id", "unknown")

        # First try to split by paragraphs
        paragraphs = self._split_by_paragraphs(text)

        current_chunk = ""
        chunk_index = 0
        start_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If single paragraph is larger than chunk size, split further
            if len(para) > self.chunk_size:
                # Add current accumulated chunk if non-empty
                if current_chunk:
                    chunk = TextChunk(
                        id=f"{doc_id}_chunk_{chunk_index}",
                        content=current_chunk.strip(),
                        document_id=doc_id,
                        metadata=metadata.copy(),
                        start_index=start_index,
                        end_index=start_index + len(current_chunk)
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    start_index = start_index + len(current_chunk) - self.chunk_overlap
                    current_chunk = ""

                # Split large paragraph
                sub_chunks = self._split_large_text(para, doc_id, metadata, chunk_index, start_index)
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                start_index = start_index + len(para) - self.chunk_overlap

            # Check if adding this paragraph would exceed chunk size
            elif len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk = TextChunk(
                    id=f"{doc_id}_chunk_{chunk_index}",
                    content=current_chunk.strip(),
                    document_id=doc_id,
                    metadata=metadata.copy(),
                    start_index=start_index,
                    end_index=start_index + len(current_chunk)
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                start_index = start_index + len(current_chunk) - len(overlap_text)
                current_chunk = overlap_text + " " + para

            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add remaining text as final chunk
        if current_chunk.strip():
            chunk = TextChunk(
                id=f"{doc_id}_chunk_{chunk_index}",
                content=current_chunk.strip(),
                document_id=doc_id,
                metadata=metadata.copy(),
                start_index=start_index,
                end_index=start_index + len(current_chunk)
            )
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines first
        paragraphs = re.split(r'\n\s*\n', text)
        return paragraphs

    def _split_large_text(
        self,
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
        start_chunk_index: int,
        start_index: int
    ) -> List[TextChunk]:
        """Split large text into smaller chunks."""
        chunks = []
        current_pos = 0
        chunk_index = start_chunk_index

        while current_pos < len(text):
            chunk_text = text[current_pos:current_pos + self.chunk_size]
            chunks.append(TextChunk(
                id=f"{doc_id}_chunk_{chunk_index}",
                content=chunk_text,
                document_id=doc_id,
                metadata=metadata.copy(),
                start_index=start_index + current_pos,
                end_index=start_index + current_pos + len(chunk_text)
            ))
            chunk_index += 1
            current_pos += self.chunk_size - self.chunk_overlap

        return chunks


class TokenChunker(BaseChunker):
    """Split text by estimated token count."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        # Rough estimate: 1 token ≈ 4 characters
        self.chunk_size = chunk_size * 4
        self.chunk_overlap = chunk_overlap * 4
        self.base_chunker = RecursiveChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text by estimated tokens."""
        return self.base_chunker.chunk(text, metadata)


class SemanticChunker(BaseChunker):
    """Split text based on semantic boundaries like sentences and paragraphs."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text at semantic boundaries."""
        if not text:
            return []

        metadata = metadata or {}
        doc_id = metadata.get("document_id", "unknown")

        # Split into sentences
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_index = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(TextChunk(
                    id=f"{doc_id}_chunk_{chunk_index}",
                    content=current_chunk.strip(),
                    document_id=doc_id,
                    metadata=metadata.copy(),
                    start_index=start_index,
                    end_index=start_index + len(current_chunk)
                ))
                chunk_index += 1

                # Keep overlap
                overlap_len = min(self.chunk_overlap, len(current_chunk))
                overlap = current_chunk[-overlap_len:]
                start_index = start_index + len(current_chunk) - overlap_len
                current_chunk = overlap + " " + sentence

            else:
                current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(TextChunk(
                id=f"{doc_id}_chunk_{chunk_index}",
                content=current_chunk.strip(),
                document_id=doc_id,
                metadata=metadata.copy(),
                start_index=start_index,
                end_index=start_index + len(current_chunk)
            ))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        return [s for s in sentences if s.strip()]


class ChunkingStrategy:
    """Factory for creating chunkers with different strategies."""

    @staticmethod
    def create(strategy: str = "recursive", **kwargs) -> BaseChunker:
        """Create a chunker based on strategy name."""
        strategies = {
            "recursive": RecursiveChunker,
            "token": TokenChunker,
            "semantic": SemanticChunker,
        }

        chunker_class = strategies.get(strategy.lower(), RecursiveChunker)
        return chunker_class(**kwargs)


class DocumentChunker:
    """High-level document chunking interface."""

    def __init__(self, strategy: str = "recursive", **chunk_kwargs):
        self.chunker = ChunkingStrategy.create(strategy, **chunk_kwargs)

    def chunk_document(self, document) -> List[TextChunk]:
        """Chunk a document object."""
        metadata = document.metadata.copy() if hasattr(document, 'metadata') else {}
        metadata["document_id"] = document.id if hasattr(document, 'id') else "unknown"

        return self.chunker.chunk(document.content, metadata)

    def chunk_documents(self, documents: List) -> List[TextChunk]:
        """Chunk multiple documents."""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks