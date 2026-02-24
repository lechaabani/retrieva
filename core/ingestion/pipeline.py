"""Ingestion pipeline: extract, clean, chunk, embed, store."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.exceptions import (
    ExtractionError,
    IngestionError,
    UnsupportedFileTypeError,
)
from core.ingestion.chunkers import get_chunker
from core.ingestion.chunkers.base import BaseChunker, Chunk
from core.ingestion.embedders.base import BaseEmbedder
from core.ingestion.extractors.base import BaseExtractor, ExtractedDocument
from core.ingestion.extractors.docx import DocxExtractor
from core.ingestion.extractors.excel import ExcelExtractor
from core.ingestion.extractors.html import HTMLExtractor
from core.ingestion.extractors.pdf import PDFExtractor
from core.ingestion.extractors.text import TextExtractor

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Outcome of an ingestion pipeline run."""

    document_id: str
    chunks_count: int
    status: str  # "success", "partial", "failed"
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


# ── Default extractor registry ────────────────────────────────────────────────

_EXTRACTOR_MAP: dict[str, type[BaseExtractor]] = {
    ".pdf": PDFExtractor,
    ".docx": DocxExtractor,
    ".xlsx": ExcelExtractor,
    ".xls": ExcelExtractor,
    ".txt": TextExtractor,
    ".md": TextExtractor,
    ".csv": TextExtractor,
    ".log": TextExtractor,
    ".rst": TextExtractor,
    ".html": HTMLExtractor,
    ".htm": HTMLExtractor,
}

# Maps file extension to plugin extractor names for plugin manager lookup.
_EXT_TO_PLUGIN: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "excel",
    ".xls": "excel",
    ".txt": "text",
    ".md": "text",
    ".csv": "text",
    ".log": "text",
    ".rst": "text",
    ".html": "html",
    ".htm": "html",
}


class IngestionPipeline:
    """Orchestrates the full ingestion lifecycle.

    Pipeline stages: extract -> clean -> transform -> chunk -> embed -> store.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: Any = None,
        chunking_strategy: str = "semantic",
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        collection_id: Optional[str] = None,
        transformers: Optional[list] = None,
    ) -> None:
        """
        Args:
            embedder: Embedding provider to use.
            vector_store: Optional VectorStore instance for persisting vectors.
            chunking_strategy: One of "fixed", "semantic", "document".
            chunk_size: Target token count per chunk (for fixed/semantic).
            chunk_overlap: Overlap tokens between chunks (for fixed chunker).
            collection_id: Target vector collection name.
            transformers: Optional list of BaseTransformer instances to apply
                between clean and chunk stages.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.collection_id = collection_id
        self.transformers = transformers or []

        # Instantiate chunker via plugin manager (with built-in fallback)
        self.chunker: BaseChunker = get_chunker(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # ── Public entry points ────────────────────────────────────────────────

    async def ingest_file(
        self,
        file_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Ingest a local file through the full pipeline.

        Args:
            file_path: Path to the file.
            metadata: Additional metadata to attach to chunks.

        Returns:
            IngestionResult describing the outcome.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        extractor = self._get_extractor(ext)
        doc = await extractor.extract(path)

        extra_meta = {"source": str(path), "source_type": "file", **(metadata or {})}
        return await self._run_pipeline(doc, extra_meta)

    async def ingest_text(
        self,
        text: str,
        title: str = "Untitled",
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Ingest raw text through the pipeline.

        Args:
            text: The text content.
            title: Document title.
            metadata: Additional metadata.

        Returns:
            IngestionResult describing the outcome.
        """
        doc = ExtractedDocument(content=text, title=title, metadata={"source_type": "text"})
        extra_meta = {"source": "direct_text", "source_type": "text", **(metadata or {})}
        return await self._run_pipeline(doc, extra_meta)

    async def ingest_url(
        self,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Ingest content from a URL.

        Args:
            url: The web URL to fetch and ingest.
            metadata: Additional metadata.

        Returns:
            IngestionResult describing the outcome.
        """
        extractor = HTMLExtractor()
        try:
            import httpx

            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_bytes = response.content
        except ImportError:
            raise IngestionError("httpx is required for URL ingestion: pip install httpx")
        except Exception as exc:
            raise IngestionError(f"Failed to fetch URL {url}: {exc}") from exc

        doc = await extractor.extract(html_bytes)
        doc.metadata["url"] = url
        extra_meta = {"source": url, "source_type": "url", **(metadata or {})}
        return await self._run_pipeline(doc, extra_meta)

    # ── Extractor resolution ─────────────────────────────────────────────

    @staticmethod
    def _get_extractor(ext: str) -> BaseExtractor:
        """Resolve an extractor for the given file extension.

        Tries the plugin manager first, then falls back to built-in extractors.
        """
        # Try plugin manager
        plugin_name = _EXT_TO_PLUGIN.get(ext)
        if plugin_name:
            try:
                from core.plugin_system.manager import get_plugin_manager

                pm = get_plugin_manager()
                return pm.get_plugin("extractor", plugin_name)
            except Exception:
                pass

        # Fallback to built-in
        cls = _EXTRACTOR_MAP.get(ext)
        if cls is None:
            raise UnsupportedFileTypeError(f"No extractor for file type '{ext}'")
        return cls()

    # ── Internal pipeline ──────────────────────────────────────────────────

    async def _run_pipeline(
        self,
        doc: ExtractedDocument,
        extra_metadata: dict[str, Any],
    ) -> IngestionResult:
        """Execute the extract -> clean -> transform -> chunk -> embed -> store pipeline."""
        document_id = str(uuid.uuid4())
        errors: list[str] = []

        try:
            # Clean
            cleaned_text = self._clean_text(doc.content)
            if not cleaned_text.strip():
                return IngestionResult(
                    document_id=document_id,
                    chunks_count=0,
                    status="failed",
                    errors=["Extracted content is empty after cleaning"],
                )

            # Transform — apply each transformer sequentially
            merged_meta = {**doc.metadata, **extra_metadata, "document_id": document_id, "title": doc.title}
            transformed_text = cleaned_text
            for transformer in self.transformers:
                try:
                    result_text, merged_meta = transformer.transform(transformed_text, merged_meta)
                    if result_text is None:
                        # Transformer signalled skip (e.g. duplicate)
                        logger.info(
                            "Document %s skipped by transformer %s",
                            document_id, getattr(transformer, "name", type(transformer).__name__),
                        )
                        return IngestionResult(
                            document_id=document_id,
                            chunks_count=0,
                            status="skipped",
                            metadata=merged_meta,
                            errors=[f"Skipped by {getattr(transformer, 'name', 'transformer')}"],
                        )
                    transformed_text = result_text
                except Exception as tx_exc:
                    logger.warning(
                        "Transformer %s failed for document %s: %s (continuing)",
                        getattr(transformer, "name", type(transformer).__name__),
                        document_id,
                        tx_exc,
                    )
                    errors.append(f"Transformer {getattr(transformer, 'name', 'unknown')}: {tx_exc}")

            # Chunk
            chunks = self.chunker.chunk(transformed_text, metadata=merged_meta)
            if not chunks:
                return IngestionResult(
                    document_id=document_id,
                    chunks_count=0,
                    status="failed",
                    errors=["Chunking produced no chunks"],
                )

            # Embed
            texts = [c.content for c in chunks]
            embeddings = await self.embedder.embed(texts)

            # Store
            if self.vector_store and self.collection_id:
                ids = [f"{document_id}_{c.position}" for c in chunks]
                payloads = [
                    {"content": c.content, **c.metadata}
                    for c in chunks
                ]
                await self.vector_store.upsert_vectors(
                    collection_name=self.collection_id,
                    ids=ids,
                    vectors=embeddings,
                    payloads=payloads,
                )

            logger.info(
                "Ingested document %s: %d chunks embedded", document_id, len(chunks)
            )
            return IngestionResult(
                document_id=document_id,
                chunks_count=len(chunks),
                status="success",
                metadata={"title": doc.title, **extra_metadata},
                errors=errors,
            )

        except ExtractionError as exc:
            logger.error("Extraction failed for document %s: %s", document_id, exc)
            return IngestionResult(
                document_id=document_id, chunks_count=0, status="failed", errors=[str(exc)]
            )
        except Exception as exc:
            logger.error("Pipeline failed for document %s: %s", document_id, exc)
            raise IngestionError(f"Ingestion pipeline failed: {exc}") from exc

    @staticmethod
    def _clean_text(text: str) -> str:
        """Basic text cleaning: normalise whitespace, remove control characters."""
        # Remove null bytes and control characters (keep newlines/tabs)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse runs of whitespace (preserving paragraph breaks)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
