"""
Day 48: Document Processing
===========================
Process various document types for RAG pipelines.

Learn to extract, parse, and prepare documents from different sources
for retrieval-augmented generation.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json
import uuid


class DocumentType(Enum):
    """Supported document types"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    JSON = "json"
    CODE = "code"
    EMAIL = "email"


@dataclass
class Document:
    """Represents a processed document"""
    id: str
    content: str
    doc_type: DocumentType
    source: str  # Original source/file path
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    embeddings: List[float] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProcessedChunk:
    """A chunk of a document"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """
    Document Processing Pipeline
    ==============================

    Process various document types into chunks for RAG.

    Pipeline:
    1. Parse document
    2. Extract sections
    3. Clean content
    4. Chunk content
    5. Add metadata
    """

    def __init__(self):
        self.processors: Dict[DocumentType, Callable] = {}

    def process(
        self,
        source: str,
        content: str = None,
        doc_type: DocumentType = None,
        content_type: str = None
    ) -> Document:
        """
        Process a document
        ===================

        1. Detect type if not provided
        2. Parse content
        3. Extract sections
        4. Clean and normalize
        """
        # Detect type
        if doc_type is None:
            doc_type = self._detect_type(source, content, content_type)

        # Get processor
        processor = self.processors.get(doc_type, self._process_text)

        # Parse
        parsed = processor(source, content)

        # Create document
        doc = Document(
            id=f"doc_{uuid.uuid4().hex[:8]}",
            content=parsed["content"],
            doc_type=doc_type,
            source=source,
            metadata=parsed.get("metadata", {}),
            sections=parsed.get("sections", [])
        )

        return doc

    def _detect_type(
        self,
        source: str,
        content: str,
        content_type: str = None
    ) -> DocumentType:
        """Detect document type"""
        # From content type header
        if content_type:
            if "markdown" in content_type.lower():
                return DocumentType.MARKDOWN
            elif "html" in content_type.lower():
                return DocumentType.HTML
            elif "pdf" in content_type.lower():
                return DocumentType.PDF
            elif "json" in content_type.lower():
                return DocumentType.JSON
            elif "csv" in content_type.lower():
                return DocumentType.CSV

        # From file extension
        if source:
            ext = source.lower().split(".")[-1] if "." in source else ""
            if ext in {"md", "markdown"}:
                return DocumentType.MARKDOWN
            elif ext == "html":
                return DocumentType.HTML
            elif ext == "pdf":
                return DocumentType.PDF
            elif ext == "docx":
                return DocumentType.DOCX
            elif ext == "csv":
                return DocumentType.CSV
            elif ext == "json":
                return DocumentType.JSON

        # From content
        if content:
            content_stripped = content.strip()
            if content_stripped.startswith("<"):
                if content_stripped.startswith("<!DOCTYPE") or content_stripped.startswith("<html"):
                    return DocumentType.HTML
            elif content_stripped.startswith("#") or "```" in content_stripped:
                return DocumentType.MARKDOWN
            elif content_stripped.startswith("{") or content_stripped.startswith("["):
                try:
                    json.loads(content_stripped)
                    return DocumentType.JSON
                except:
                    pass

        return DocumentType.TEXT

    def _process_text(
        self,
        source: str,
        content: str
    ) -> Dict[str, Any]:
        """Process plain text"""
        return {
            "content": content,
            "sections": [{"title": "全文", "content": content}],
            "metadata": {"char_count": len(content)}
        }

    def _process_markdown(
        self,
        source: str,
        content: str
    ) -> Dict[str, Any]:
        """Process Markdown document"""
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        lines = content.split("\n")

        for line in lines:
            # Detect headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                if current_section["content"].strip():
                    sections.append(current_section)
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = {"title": title, "content": "", "level": level}
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        full_content = "\n".join(s.get("content", "") for s in sections)

        return {
            "content": full_content,
            "sections": sections,
            "metadata": {
                "char_count": len(content),
                "section_count": len(sections)
            }
        }

    def _process_html(
        self,
        source: str,
        content: str
    ) -> Dict[str, Any]:
        """Process HTML document"""
        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Extract text
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()

        # Extract title
        title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1) if title_match else "Untitled"

        return {
            "content": text,
            "sections": [{"title": title, "content": text}],
            "metadata": {"char_count": len(text)}
        }

    def _process_json(
        self,
        source: str,
        content: str
    ) -> Dict[str, Any]:
        """Process JSON document"""
        try:
            data = json.loads(content)
        except:
            return self._process_text(source, content)

        # Flatten for text representation
        def flatten(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key))
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten(item, f"{new_key}[{i}]"))
                        else:
                            items.append((f"{new_key}[{i}]", str(item)))
                else:
                    items.append((new_key, str(v)))
            return items

        text = "\n".join(f"{k}: {v}" for k, v in flatten(data))

        return {
            "content": text,
            "sections": [{"title": "Data", "content": text}],
            "metadata": {"char_count": len(text)}
        }

    def _process_csv(
        self,
        source: str,
        content: str
    ) -> Dict[str, Any]:
        """Process CSV document"""
        lines = content.strip().split("\n")
        if not lines:
            return {"content": "", "sections": [], "metadata": {}}

        headers = lines[0].split(",")
        rows = [line.split(",") for line in lines[1:]]

        # Format as text
        text = content  # Keep original CSV

        sections = [{"title": f"Row {i+1}", "content": ", ".join(row)} for i, row in enumerate(rows)]

        return {
            "content": text,
            "sections": sections,
            "metadata": {
                "row_count": len(rows),
                "column_count": len(headers),
                "headers": headers
            }
        }

    def chunk(
        self,
        document: Document,
        chunk_size: int = 500,
        overlap: int = 50,
        strategy: str = "by_section"
    ) -> List[ProcessedChunk]:
        """
        Chunk document into smaller pieces
        ===================================

        Strategies:
        - by_section: Split by sections
        - by_tokens: Split by token count
        - by_paragraphs: Split by paragraphs
        """
        if strategy == "by_section":
            return self._chunk_by_section(document, chunk_size, overlap)
        elif strategy == "by_paragraphs":
            return self._chunk_by_paragraphs(document, chunk_size, overlap)
        else:
            return self._chunk_by_tokens(document, chunk_size, overlap)

    def _chunk_by_section(
        self,
        document: Document,
        chunk_size: int,
        overlap: int
    ) -> List[ProcessedChunk]:
        """Chunk by section boundaries"""
        chunks = []

        for i, section in enumerate(document.sections):
            content = section.get("content", "")
            title = section.get("title", f"Section {i+1}")

            # If section is too large, split further
            if len(content) > chunk_size:
                sub_chunks = self._split_text(content, chunk_size, overlap)
                for j, sub_content in enumerate(sub_chunks):
                    chunks.append(ProcessedChunk(
                        id=f"chunk_{uuid.uuid4().hex[:8]}",
                        document_id=document.id,
                        content=f"{title}\n\n{sub_content}",
                        chunk_index=len(chunks),
                        start_char=0,
                        end_char=len(sub_content),
                        metadata={
                            "section": title,
                            "sub_chunk": j
                        }
                    ))
            else:
                chunks.append(ProcessedChunk(
                    id=f"chunk_{uuid.uuid4().hex[:8]}",
                    document_id=document.id,
                    content=f"{title}\n\n{content}",
                    chunk_index=len(chunks),
                    start_char=0,
                    end_char=len(content),
                    metadata={"section": title}
                ))

        return chunks

    def _chunk_by_paragraphs(
        self,
        document: Document,
        chunk_size: int,
        overlap: int
    ) -> List[ProcessedChunk]:
        """Chunk by paragraphs"""
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', document.content)

        chunks = []
        current_chunk = ""
        start_char = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(ProcessedChunk(
                        id=f"chunk_{uuid.uuid4().hex[:8]}",
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=len(chunks),
                        start_char=start_char,
                        end_char=start_char + len(current_chunk),
                        metadata={}
                    ))

                # Handle overlap
                if overlap > 0 and chunks:
                    prev_chunk = chunks[-1].content
                    current_chunk = prev_chunk[-overlap:] + para + "\n\n"
                    start_char = chunks[-1].end_char - overlap
                else:
                    current_chunk = para + "\n\n"
                    start_char = chunks[-1].end_char if chunks else 0

        # Last chunk
        if current_chunk.strip():
            chunks.append(ProcessedChunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=len(chunks),
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={}
            ))

        return chunks

    def _chunk_by_tokens(
        self,
        document: Document,
        chunk_size: int,
        overlap: int
    ) -> List[ProcessedChunk]:
        """Chunk by approximate token count"""
        # Simple token estimation (1 token ~= 4 chars)
        token_size = chunk_size // 4
        overlap_tokens = overlap // 4

        return self._chunk_by_paragraphs(document, token_size * 4, overlap * 4)

    def _split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])

            # Move with overlap
            start = end - overlap if end < len(text) else end

        return chunks

    def register_processor(
        self,
        doc_type: DocumentType,
        processor: Callable
    ):
        """Register custom processor"""
        self.processors[doc_type] = processor


# Demo function
def demo():
    """Demonstrate Document Processing"""
    print("=" * 60)
    print("  Document Processing Demo")
    print("=" * 60)

    processor = DocumentProcessor()

    # Test with Markdown
    print("\n1. Processing Markdown...")
    markdown = """# Agent OS Documentation

## Introduction

Agent OS is a platform for building AI agents.

## Installation

```bash
pip install agentos
```

## Quick Start

Create your first agent:

```python
from agentos import Agent

agent = Agent()
agent.run("Hello!")
```
"""
    doc = processor.process("docs/README.md", markdown, DocumentType.MARKDOWN)
    print(f"   Document ID: {doc.id}")
    print(f"   Sections: {len(doc.sections)}")
    print(f"   Content length: {len(doc.content)} chars")

    # Chunk the document
    print("\n2. Chunking document...")
    chunks = processor.chunk(doc, chunk_size=200, overlap=30)
    print(f"   Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"   Chunk {i}: {chunk.content[:50]}...")

    # Process JSON
    print("\n3. Processing JSON...")
    json_data = json.dumps({
        "name": "AgentOS",
        "version": "1.0.0",
        "features": ["memory", "tools", "multi-agent"]
    }, indent=2)
    doc = processor.process("config.json", json_data, DocumentType.JSON)
    print(f"   Content: {doc.content[:100]}...")

    # Process HTML
    print("\n4. Processing HTML...")
    html = """<html>
<head><title>AgentOS</title></head>
<body>
<h1>Welcome to AgentOS</h1>
<p>Build intelligent agents with ease.</p>
</body>
</html>"""
    doc = processor.process("index.html", html)
    print(f"   Title from metadata: {doc.metadata}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()