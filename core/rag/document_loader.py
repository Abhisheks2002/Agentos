"""Document Loaders for Agentic RAG - Day 10 Implementation."""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class Document:
    """Represents a document with its content and metadata."""

    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.id = f"doc_{datetime.now().timestamp()}"
        self.content = content
        self.metadata = metadata or {}
        self.metadata["created_at"] = datetime.now().isoformat()

    def __repr__(self):
        return f"Document(id={self.id}, content_length={len(self.content)})"


class BaseLoader(ABC):
    """Base class for document loaders."""

    @abstractmethod
    def load(self, source: str) -> List[Document]:
        """Load documents from source."""
        pass


class TextLoader(BaseLoader):
    """Load plain text files."""

    def load(self, source: str) -> List[Document]:
        """Load text file."""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                "source": source,
                "file_type": "text",
                "file_name": os.path.basename(source)
            }

            return [Document(content, metadata)]
        except Exception as e:
            logger.error(f"Error loading text file {source}: {e}")
            return []


class MarkdownLoader(BaseLoader):
    """Load markdown files."""

    def load(self, source: str) -> List[Document]:
        """Load markdown file."""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                "source": source,
                "file_type": "markdown",
                "file_name": os.path.basename(source)
            }

            return [Document(content, metadata)]
        except Exception as e:
            logger.error(f"Error loading markdown file {source}: {e}")
            return []


class HTMLLoader(BaseLoader):
    """Load HTML files."""

    def load(self, source: str) -> List[Document]:
        """Load HTML file and extract text."""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Simple HTML to text conversion
            text = self._extract_text(html_content)

            metadata = {
                "source": source,
                "file_type": "html",
                "file_name": os.path.basename(source)
            }

            return [Document(text, metadata)]
        except Exception as e:
            logger.error(f"Error loading HTML file {source}: {e}")
            return []

    def _extract_text(self, html: str) -> str:
        """Extract text from HTML."""
        import re
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Replace tags with newlines
        text = re.sub(r'<[^>]+>', '\n', text)
        # Remove extra whitespace
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()
        return text


class PDFLoader(BaseLoader):
    """Load PDF files."""

    def load(self, source: str) -> List[Document]:
        """Load PDF file and extract text."""
        try:
            # Try to import pypdf
            try:
                from pypdf import PdfReader
            except ImportError:
                logger.warning("pypdf not installed. Attempting to use pdfminer.")
                return self._load_with_pdfminer(source)

            reader = PdfReader(source)
            documents = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    metadata = {
                        "source": source,
                        "file_type": "pdf",
                        "file_name": os.path.basename(source),
                        "page": page_num + 1,
                        "total_pages": len(reader.pages)
                    }
                    documents.append(Document(text, metadata))

            return documents

        except Exception as e:
            logger.error(f"Error loading PDF file {source}: {e}")
            return []

    def _load_with_pdfminer(self, source: str) -> List[Document]:
        """Fallback PDF loading using pdfminer."""
        try:
            from pdfminer.high_level import extract_text

            text = extract_text(source)
            metadata = {
                "source": source,
                "file_type": "pdf",
                "file_name": os.path.basename(source)
            }

            return [Document(text, metadata)] if text.strip() else []
        except Exception as e:
            logger.error(f"Error with pdfminer for {source}: {e}")
            return []


class JSONLoader(BaseLoader):
    """Load JSON files."""

    def load(self, source: str) -> List[Document]:
        """Load JSON file."""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert JSON to formatted text
            content = json.dumps(data, indent=2)

            metadata = {
                "source": source,
                "file_type": "json",
                "file_name": os.path.basename(source)
            }

            return [Document(content, metadata)]
        except Exception as e:
            logger.error(f"Error loading JSON file {source}: {e}")
            return []


class DirectoryLoader(BaseLoader):
    """Load all supported files from a directory."""

    def __init__(self, recursive: bool = True):
        self.recursive = recursive
        self.loaders = {
            '.txt': TextLoader(),
            '.md': MarkdownLoader(),
            '.html': HTMLLoader(),
            '.htm': HTMLLoader(),
            '.pdf': PDFLoader(),
            '.json': JSONLoader(),
        }

    def load(self, source: str) -> List[Document]:
        """Load all supported files from directory."""
        documents = []
        path = Path(source)

        if not path.is_dir():
            logger.error(f"Source is not a directory: {source}")
            return []

        pattern = "**/*" if self.recursive else "*"

        for file_path in path.glob(pattern):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.loaders:
                    loader = self.loaders[ext]
                    docs = loader.load(str(file_path))
                    documents.extend(docs)

        logger.info(f"Loaded {len(documents)} documents from {source}")
        return documents


class DocumentLoaderFactory:
    """Factory for creating document loaders based on file type."""

    _loaders = {
        '.txt': TextLoader,
        '.md': MarkdownLoader,
        '.html': HTMLLoader,
        '.htm': HTMLLoader,
        '.pdf': PDFLoader,
        '.json': JSONLoader,
    }

    @classmethod
    def get_loader(cls, file_path: str) -> Optional[BaseLoader]:
        """Get appropriate loader for file type."""
        ext = Path(file_path).suffix.lower()
        loader_class = cls._loaders.get(ext)
        if loader_class:
            return loader_class()
        return None

    @classmethod
    def load(cls, file_path: str) -> List[Document]:
        """Load document using appropriate loader."""
        loader = cls.get_loader(file_path)
        if loader:
            return loader.load(file_path)
        logger.warning(f"No loader available for file type: {file_path}")
        return []