"""
Day 49: Chunking Strategies
=============================
Advanced text chunking strategies for optimal RAG retrieval.

Different chunking strategies for different use cases:
- Fixed size
- Sentence-based
- Semantic
- Recursive
- Markdown-aware
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import uuid


@dataclass
class Chunk:
    """A text chunk"""
    id: str
    content: str
    start_idx: int
    end_idx: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class ChunkingStrategy:
    """Base class for chunking strategies"""

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        raise NotImplementedError


class FixedSizeChunking(ChunkingStrategy):
    """
    Fixed Size Chunking
    ====================

    Split text into fixed-size chunks.
    Simple but may break sentences.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end]

            chunks.append(Chunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=content,
                start_idx=start,
                end_idx=end,
                metadata={
                    "strategy": "fixed_size",
                    "chunk_size": self.chunk_size,
                    "overlap": self.overlap
                }
            ))

            # Move start position with overlap
            start = end - self.overlap if end < len(text) else end

        return chunks


class SentenceChunking(ChunkingStrategy):
    """
    Sentence-based Chunking
    ========================

    Split by sentences, group into chunks.
    Better preserves semantic meaning.
    """

    def __init__(self, chunk_size: int = 3, overlap: int = 1):
        self.chunk_size = chunk_size  # Number of sentences per chunk
        self.overlap = overlap  # Number of sentences to overlap

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Common sentence endings
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        sentences = self._split_sentences(text)
        chunks = []

        for i in range(0, len(sentences), self.chunk_size - self.overlap):
            chunk_sentences = sentences[i:i + self.chunk_size]
            content = ' '.join(chunk_sentences)

            start_idx = text.index(chunk_sentences[0]) if chunk_sentences else 0
            end_idx = start_idx + len(content)

            chunks.append(Chunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=content,
                start_idx=start_idx,
                end_idx=end_idx,
                metadata={
                    "strategy": "sentence",
                    "sentence_count": len(chunk_sentences)
                }
            ))

            # Stop if we've covered all sentences
            if i + self.chunk_size >= len(sentences):
                break

        return chunks


class RecursiveChunking(ChunkingStrategy):
    """
    Recursive Chunking
    ==================

    Split text hierarchically:
    1. Try to split on double newlines (paragraphs)
    2. Then single newlines
    3. Then sentences
    4. Then words
    5. Finally characters

    This preserves meaningful chunks while respecting boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Default separators in order of preference
        self.separators = separators or [
            "\n\n",   # Paragraphs
            "\n",     # Lines
            ". ",     # Sentences
            "; ",     # Clauses
            ", ",     # Phrases
            " "       # Words
        ]

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        chunks = []
        self._split_recursive(text, self.separators, chunks)

        # Merge small chunks
        chunks = self._merge_small_chunks(chunks)

        # Add overlap
        chunks = self._add_overlap(chunks, text)

        # Re-index
        for i, chunk in enumerate(chunks):
            chunk.metadata["index"] = i

        return chunks

    def _split_recursive(
        self,
        text: str,
        separators: List[str],
        chunks: List[Chunk],
        start_idx: int = 0
    ):
        """Recursively split text"""
        if not text:
            return

        # Try current separator
        separator = separators[0]
        remaining_separators = separators[1:]

        parts = text.split(separator)

        if len(parts) == 1 or not remaining_separators:
            # Can't split more or no more separators
            if len(text) <= self.chunk_size:
                chunks.append(Chunk(
                    id=f"chunk_{uuid.uuid4().hex[:8]}",
                    content=text,
                    start_idx=start_idx,
                    end_idx=start_idx + len(text),
                    metadata={"strategy": "recursive"}
                ))
            else:
                # Force split at chunk size
                for i in range(0, len(text), self.chunk_size):
                    chunk_text = text[i:i + self.chunk_size]
                    chunks.append(Chunk(
                        id=f"chunk_{uuid.uuid4().hex[:8]}",
                        content=chunk_text,
                        start_idx=start_idx + i,
                        end_idx=start_idx + i + len(chunk_text),
                        metadata={"strategy": "recursive"}
                    ))
            return

        # Process parts
        current_start = start_idx
        for part in parts:
            if not part.strip():
                current_start += len(separator)
                continue

            if len(part) <= self.chunk_size:
                chunks.append(Chunk(
                    id=f"chunk_{uuid.uuid4().hex[:8]}",
                    content=part,
                    start_idx=current_start,
                    end_idx=current_start + len(part),
                    metadata={"strategy": "recursive"}
                ))
            else:
                # Recurse with fewer separators
                self._split_recursive(part, remaining_separators, chunks, current_start)

            current_start += len(part) + len(separator)

    def _merge_small_chunks(self, chunks: List[Chunk], min_size: int = 100) -> List[Chunk]:
        """Merge small chunks with neighbors"""
        if not chunks:
            return []

        merged = [chunks[0]]

        for chunk in chunks[1:]:
            last = merged[-1]

            # Merge if either is too small
            if len(last.content) < min_size or len(chunk.content) < min_size:
                merged[-1] = Chunk(
                    id=last.id,
                    content=last.content + " " + chunk.content,
                    start_idx=last.start_idx,
                    end_idx=chunk.end_idx,
                    metadata={"strategy": "recursive", "merged": True}
                )
            else:
                merged.append(chunk)

        return merged

    def _add_overlap(self, chunks: List[Chunk], text: str) -> List[Chunk]:
        """Add overlap between chunks"""
        if not chunks or self.overlap == 0:
            return chunks

        # Note: In production, would adjust actual content
        for chunk in chunks:
            chunk.metadata["overlap"] = self.overlap

        return chunks


class SemanticChunking(ChunkingStrategy):
    """
    Semantic Chunking
    ==================

    Use embeddings to find natural semantic boundaries.
    Groups text by semantic similarity.
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def _embed_simulate(self, text: str) -> List[float]:
        """Simulate embedding (in production use real embeddings)"""
        import hashlib
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        embedding = []
        for i in range(0, len(hash_val), 8):
            chunk = hash_val[i:i+8]
            val = int(chunk, 16) / (16**8) * 2 - 1
            embedding.append(val)
        while len(embedding) < 64:
            embedding.append(0.0)
        return embedding[:64]

    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity"""
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(y * y for y in b) ** 0.5
        return dot / (mag_a * mag_b) if mag_a * mag_b > 0 else 0

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        # Split into sentences first
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return [Chunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=text,
                start_idx=0,
                end_idx=len(text),
                metadata={"strategy": "semantic"}
            )]

        # Compute embeddings for each sentence
        embeddings = [self._embed_simulate(s) for s in sentences]

        # Find boundaries where similarity drops
        chunks = []
        current_chunk = [sentences[0]]
        current_start = 0

        for i in range(1, len(sentences)):
            # Compute similarity between current and next
            similarity = self._cosine_sim(embeddings[i-1], embeddings[i])

            if similarity < self.threshold:
                # Create chunk
                content = ' '.join(current_chunk)
                chunks.append(Chunk(
                    id=f"chunk_{uuid.uuid4().hex[:8]}",
                    content=content,
                    start_idx=current_start,
                    end_idx=current_start + len(content),
                    metadata={
                        "strategy": "semantic",
                        "sentence_count": len(current_chunk)
                    }
                ))

                current_chunk = [sentences[i]]
                current_start = text.index(sentences[i])
            else:
                current_chunk.append(sentences[i])

        # Last chunk
        if current_chunk:
            content = ' '.join(current_chunk)
            chunks.append(Chunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=content,
                start_idx=current_start,
                end_idx=current_start + len(content),
                metadata={
                    "strategy": "semantic",
                    "sentence_count": len(current_chunk)
                }
            ))

        return chunks


class MarkdownChunking(ChunkingStrategy):
    """
    Markdown-aware Chunking
    =======================

    Preserve markdown structure when chunking.
    Headers become chunk boundaries.
    """

    def __init__(self, include_metadata: bool = True):
        self.include_metadata = include_metadata

    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        chunks = []
        lines = text.split("\n")

        current_section = None
        current_content = []
        current_start = 0

        for i, line in enumerate(lines):
            # Check for header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # Save previous section
                if current_content:
                    content = "\n".join(current_content).strip()
                    chunks.append(Chunk(
                        id=f"chunk_{uuid.uuid4().hex[:8]}",
                        content=content,
                        start_idx=current_start,
                        end_idx=current_start + len(content),
                        metadata={
                            "strategy": "markdown",
                            "section": current_section,
                            "header_level": header_match.group(1).__len__()
                        }
                    ))

                # Start new section
                current_section = header_match.group(2)
                current_content = [line]
                current_start = text.index(line)
            else:
                current_content.append(line)

        # Last section
        if current_content:
            content = "\n".join(current_content).strip()
            chunks.append(Chunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=content,
                start_idx=current_start,
                end_idx=current_start + len(content),
                metadata={
                    "strategy": "markdown",
                    "section": current_section
                }
            ))

        return chunks


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies"""

    STRATEGIES = {
        "fixed": FixedSizeChunking,
        "sentence": SentenceChunking,
        "recursive": RecursiveChunking,
        "semantic": SemanticChunking,
        "markdown": MarkdownChunking
    }

    @classmethod
    def create(
        cls,
        strategy: str,
        **kwargs
    ) -> ChunkingStrategy:
        """Create a chunking strategy"""
        strategy_class = cls.STRATEGIES.get(strategy.lower())
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy}")

        return strategy_class(**kwargs)


# Demo function
def demo():
    """Demonstrate Chunking Strategies"""
    print("=" * 60)
    print("  Chunking Strategies Demo")
    print("=" * 60)

    text = """Agent OS is a powerful platform for building AI agents. It provides memory, tools, and multi-agent collaboration capabilities.

Installation is simple: pip install agentos. Then create your first agent with just a few lines of code.

The agent can use tools to interact with external systems. Tools can be anything from API calls to database queries. Each tool has a name, description, and parameters.

Memory is crucial for agentic behavior. Agent OS supports various memory types: short-term, long-term, and semantic memory. Short-term memory holds the current conversation context. Long-term memory persists across sessions.

Multi-agent collaboration enables complex workflows. Agents can communicate, delegate tasks, and reach consensus. This is powered by the agent orchestration layer."""

    print("\n" + "-" * 50)
    print("Test text:")
    print(text[:200] + "...")
    print("-" * 50)

    # Test each strategy
    strategies = [
        ("Fixed Size", FixedSizeChunking(chunk_size=150, overlap=20)),
        ("Sentence", SentenceChunking(chunk_size=2, overlap=1)),
        ("Recursive", RecursiveChunking(chunk_size=150, overlap=30)),
        ("Semantic", SemanticChunking(threshold=0.3)),
        ("Markdown", MarkdownChunking())
    ]

    for name, strategy in strategies:
        print(f"\n{name} Chunking:")
        chunks = strategy.chunk(text)

        print(f"  Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i}: {chunk.content[:60]}...")
            print(f"    Length: {len(chunk.content)} chars")

    # Compare strategies
    print("\n" + "=" * 50)
    print("Strategy Comparison:")
    print("=" * 50)

    for name, strategy in strategies:
        chunks = strategy.chunk(text)
        avg_length = sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0
        print(f"  {name:15} | Chunks: {len(chunks):2} | Avg length: {avg_length:.0f}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()