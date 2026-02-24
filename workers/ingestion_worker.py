"""Celery tasks for document ingestion.

Handles file, text, and URL ingestion through the core pipeline,
updating document status in PostgreSQL as processing proceeds.
All database access is synchronous since Celery workers do not
run inside an asyncio event loop.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from celery import Task

from workers.celery_app import app
from workers.db import get_sync_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run an async coroutine synchronously for use in Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _dispatch_webhook(event: str, data: dict[str, Any], tenant_id: str | None = None) -> None:
    """Fire a webhook notification, swallowing errors so ingestion is never blocked."""
    try:
        from core.webhooks import WebhookDispatcher

        if not tenant_id:
            # Try to look up tenant_id from the document
            doc_id = data.get("document_id")
            if doc_id:
                with get_sync_session() as session:
                    from api.models.document import Document

                    doc = session.get(Document, uuid.UUID(doc_id))
                    if doc and doc.collection:
                        tenant_id = str(doc.collection.tenant_id)

        if tenant_id:
            dispatcher = WebhookDispatcher(tenant_id=tenant_id)
            dispatcher.dispatch_sync(event, data, tenant_id=tenant_id)
    except Exception as exc:
        logger.warning("Webhook dispatch failed (non-fatal): %s", exc)


def _set_document_status(
    document_id: str,
    status: str,
    *,
    chunks_count: int | None = None,
    error_detail: str | None = None,
) -> None:
    """Update document status and optional fields in the database."""
    from api.models.document import Document, DocumentStatus

    with get_sync_session() as session:
        doc = session.get(Document, uuid.UUID(document_id))
        if doc is None:
            logger.error("Document %s not found in database", document_id)
            return

        doc.status = DocumentStatus(status)

        if chunks_count is not None:
            doc.chunks_count = chunks_count

        if status == "indexed":
            doc.indexed_at = datetime.now(timezone.utc)

        if error_detail:
            meta = dict(doc.doc_metadata) if doc.doc_metadata else {}
            meta["error"] = error_detail
            doc.doc_metadata = meta

        session.add(doc)


def _get_extractor_for_file(file_path: str):
    """Return the appropriate extractor instance for a file extension.

    Tries the plugin manager first, then falls back to built-in extractors.
    """
    ext = Path(file_path).suffix.lower()

    # Map extensions to plugin names
    ext_to_plugin = {
        ".pdf": "pdf", ".docx": "docx", ".xlsx": "excel", ".xls": "excel",
        ".txt": "text", ".md": "text", ".csv": "text", ".log": "text",
        ".rst": "text", ".html": "html", ".htm": "html",
    }

    plugin_name = ext_to_plugin.get(ext)
    if plugin_name:
        try:
            from core.plugin_system.manager import get_plugin_manager

            pm = get_plugin_manager()
            return pm.get_plugin("extractor", plugin_name)
        except Exception:
            pass

    # Fallback to built-in extractors
    from core.ingestion.extractors import (
        PDFExtractor,
        DocxExtractor,
        ExcelExtractor,
        TextExtractor,
        HTMLExtractor,
    )

    extractors = [
        PDFExtractor(),
        DocxExtractor(),
        ExcelExtractor(),
        TextExtractor(),
        HTMLExtractor(),
    ]
    for extractor in extractors:
        if extractor.can_handle(ext):
            return extractor

    raise ValueError(f"No extractor available for file extension: {ext}")


def _compute_content_hash(content: str) -> str:
    """Compute a SHA-256 hash of the content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _run_ingestion_pipeline(
    document_id: str,
    content: str,
    title: str,
    collection_id: str,
    config: dict[str, Any],
    source_metadata: dict[str, Any] | None = None,
) -> int:
    """Execute the chunking, embedding, and vector store pipeline.

    Returns the number of chunks created.
    """
    from core.ingestion.chunkers import get_chunker
    from core.ingestion.embedders import get_embedder
    from core.vector_store import VectorStore
    from core.config import get_config
    from api.models.chunk import Chunk

    platform_cfg = get_config()

    # --- Chunking ---
    chunk_strategy = config.get(
        "chunking_strategy", platform_cfg.ingestion.default_chunking_strategy
    )
    chunk_size = config.get("chunk_size", platform_cfg.ingestion.default_chunk_size)
    chunk_overlap = config.get("chunk_overlap", platform_cfg.ingestion.chunk_overlap)

    chunker = get_chunker(
        strategy=chunk_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    text_chunks = chunker.chunk(content)

    if not text_chunks:
        logger.warning("No chunks produced for document %s", document_id)
        return 0

    # --- Embedding ---
    embedder = get_embedder(
        provider=config.get("embedding_provider", platform_cfg.ingestion.embedding_provider),
        model=config.get("embedding_model", platform_cfg.ingestion.default_embedding_model),
    )
    embeddings = _run_async(
        embedder.embed_batch([c.content for c in text_chunks])
    )

    # --- Store in Qdrant ---
    vector_store = VectorStore(config=platform_cfg.vector_db)
    vector_ids: list[str] = []
    points = []
    for idx, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
        vector_id = str(uuid.uuid4())
        vector_ids.append(vector_id)
        payload = {
            "document_id": document_id,
            "collection_id": collection_id,
            "content": chunk.content,
            "position": idx,
            "title": title,
            **(source_metadata or {}),
            **(chunk.metadata if hasattr(chunk, "metadata") else {}),
        }
        points.append({
            "id": vector_id,
            "vector": embedding,
            "payload": payload,
        })

    vector_store.upsert(collection_id=collection_id, points=points)

    # --- Persist chunks to PostgreSQL ---
    content_hash = _compute_content_hash(content)
    with get_sync_session() as session:
        from api.models.document import Document

        doc = session.get(Document, uuid.UUID(document_id))
        if doc:
            doc.content_hash = content_hash

        for idx, (chunk, vid) in enumerate(zip(text_chunks, vector_ids)):
            db_chunk = Chunk(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                collection_id=uuid.UUID(collection_id),
                content=chunk.content,
                position=idx,
                chunk_metadata=chunk.metadata if hasattr(chunk, "metadata") else {},
                vector_id=vid,
            )
            session.add(db_chunk)

    return len(text_chunks)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@app.task(
    bind=True,
    name="workers.ingestion_worker.ingest_file",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_backoff_max=300,
    acks_late=True,
)
def ingest_file(
    self: Task,
    document_id: str,
    file_path: str,
    collection_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ingest a file through the extraction and ingestion pipeline.

    Args:
        document_id: UUID of the document record in PostgreSQL.
        file_path: Absolute path to the file on disk.
        collection_id: UUID of the target collection.
        config: Optional ingestion configuration overrides.

    Returns:
        A dict with document_id, status, and chunks_count.
    """
    config = config or {}
    logger.info(
        "Starting file ingestion: document=%s file=%s collection=%s",
        document_id, file_path, collection_id,
    )

    _set_document_status(document_id, "processing")

    try:
        # Extract content from file
        extractor = _get_extractor_for_file(file_path)
        extracted = _run_async(extractor.extract(file_path))

        if extracted.is_empty:
            _set_document_status(
                document_id, "error",
                error_detail="Extraction produced empty content",
            )
            return {
                "document_id": document_id,
                "status": "error",
                "error": "Empty content after extraction",
            }

        # Run pipeline
        chunks_count = _run_ingestion_pipeline(
            document_id=document_id,
            content=extracted.content,
            title=extracted.title or Path(file_path).stem,
            collection_id=collection_id,
            config=config,
            source_metadata=extracted.metadata,
        )

        _set_document_status(document_id, "indexed", chunks_count=chunks_count)

        _dispatch_webhook("document_indexed", {
            "document_id": document_id,
            "file_path": file_path,
            "collection_id": collection_id,
            "chunks_count": chunks_count,
        })

        logger.info(
            "File ingestion complete: document=%s chunks=%d",
            document_id, chunks_count,
        )
        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks_count": chunks_count,
        }

    except (ConnectionError, TimeoutError, OSError):
        # Let Celery's autoretry handle transient errors
        raise

    except Exception as exc:
        error_detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        logger.error(
            "File ingestion failed: document=%s error=%s",
            document_id, exc, exc_info=True,
        )
        _set_document_status(document_id, "error", error_detail=error_detail)

        _dispatch_webhook("document_error", {
            "document_id": document_id,
            "file_path": file_path,
            "collection_id": collection_id,
            "error": str(exc),
        })

        return {
            "document_id": document_id,
            "status": "error",
            "error": str(exc),
        }


@app.task(
    bind=True,
    name="workers.ingestion_worker.ingest_text",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    acks_late=True,
)
def ingest_text(
    self: Task,
    document_id: str,
    content: str,
    title: str,
    collection_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ingest raw text content through the ingestion pipeline.

    Args:
        document_id: UUID of the document record in PostgreSQL.
        content: Raw text content to ingest.
        title: Document title.
        collection_id: UUID of the target collection.
        config: Optional ingestion configuration overrides.

    Returns:
        A dict with document_id, status, and chunks_count.
    """
    config = config or {}
    logger.info(
        "Starting text ingestion: document=%s title='%s' collection=%s",
        document_id, title, collection_id,
    )

    _set_document_status(document_id, "processing")

    try:
        if not content or not content.strip():
            _set_document_status(
                document_id, "error",
                error_detail="Empty text content provided",
            )
            return {
                "document_id": document_id,
                "status": "error",
                "error": "Empty text content",
            }

        chunks_count = _run_ingestion_pipeline(
            document_id=document_id,
            content=content,
            title=title,
            collection_id=collection_id,
            config=config,
        )

        _set_document_status(document_id, "indexed", chunks_count=chunks_count)

        _dispatch_webhook("document_indexed", {
            "document_id": document_id,
            "title": title,
            "collection_id": collection_id,
            "chunks_count": chunks_count,
        })

        logger.info(
            "Text ingestion complete: document=%s chunks=%d",
            document_id, chunks_count,
        )
        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks_count": chunks_count,
        }

    except (ConnectionError, TimeoutError):
        raise

    except Exception as exc:
        error_detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        logger.error(
            "Text ingestion failed: document=%s error=%s",
            document_id, exc, exc_info=True,
        )
        _set_document_status(document_id, "error", error_detail=error_detail)

        _dispatch_webhook("document_error", {
            "document_id": document_id,
            "title": title,
            "collection_id": collection_id,
            "error": str(exc),
        })

        return {
            "document_id": document_id,
            "status": "error",
            "error": str(exc),
        }


@app.task(
    bind=True,
    name="workers.ingestion_worker.ingest_url",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    acks_late=True,
)
def ingest_url(
    self: Task,
    document_id: str,
    url: str,
    collection_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ingest content from a URL using the URL crawler connector.

    Crawls the URL (and optionally linked pages based on config), then
    ingests each page's content through the pipeline.

    Args:
        document_id: UUID of the parent document record.
        url: The URL to crawl and ingest.
        collection_id: UUID of the target collection.
        config: Optional configuration (max_pages, follow_links, etc.).

    Returns:
        A dict with document_id, status, chunks_count, and pages_crawled.
    """
    config = config or {}
    logger.info(
        "Starting URL ingestion: document=%s url=%s collection=%s",
        document_id, url, collection_id,
    )

    _set_document_status(document_id, "processing")

    try:
        from core.connectors.url_crawler import URLCrawlerConnector

        crawler = URLCrawlerConnector(config=config)
        pages = _run_async(crawler.crawl(url))

        if not pages:
            _set_document_status(
                document_id, "error",
                error_detail=f"No content crawled from URL: {url}",
            )
            return {
                "document_id": document_id,
                "status": "error",
                "error": "No content crawled",
            }

        total_chunks = 0

        # Ingest the first page under the original document_id
        first_page = pages[0]
        chunks_count = _run_ingestion_pipeline(
            document_id=document_id,
            content=first_page.get("content", ""),
            title=first_page.get("title", url),
            collection_id=collection_id,
            config=config,
            source_metadata={"source_url": first_page.get("url", url)},
        )
        total_chunks += chunks_count

        # Queue additional pages as separate ingestion tasks
        for page in pages[1:]:
            page_content = page.get("content", "")
            page_title = page.get("title", page.get("url", ""))
            if page_content and page_content.strip():
                ingest_text.delay(
                    document_id=str(uuid.uuid4()),
                    content=page_content,
                    title=page_title,
                    collection_id=collection_id,
                    config=config,
                )

        _set_document_status(document_id, "indexed", chunks_count=chunks_count)

        logger.info(
            "URL ingestion complete: document=%s pages=%d chunks=%d",
            document_id, len(pages), total_chunks,
        )
        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks_count": chunks_count,
            "pages_crawled": len(pages),
        }

    except (ConnectionError, TimeoutError):
        raise

    except Exception as exc:
        error_detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        logger.error(
            "URL ingestion failed: document=%s error=%s",
            document_id, exc, exc_info=True,
        )
        _set_document_status(document_id, "error", error_detail=error_detail)
        return {
            "document_id": document_id,
            "status": "error",
            "error": str(exc),
        }


@app.task(
    name="workers.ingestion_worker.delete_document_vectors",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    acks_late=True,
)
def delete_document_vectors(
    document_id: str,
    vector_ids: list[str],
) -> dict[str, Any]:
    """Delete vectors from Qdrant when a document is removed.

    Args:
        document_id: UUID of the document being deleted.
        vector_ids: List of vector IDs to remove from the vector store.

    Returns:
        A dict with document_id and deleted_count.
    """
    logger.info(
        "Deleting vectors: document=%s count=%d",
        document_id, len(vector_ids),
    )

    try:
        from core.vector_store import VectorStore
        from core.config import get_config

        platform_cfg = get_config()
        vector_store = VectorStore(config=platform_cfg.vector_db)
        vector_store.delete(vector_ids=vector_ids)

        logger.info(
            "Vector deletion complete: document=%s deleted=%d",
            document_id, len(vector_ids),
        )
        return {
            "document_id": document_id,
            "deleted_count": len(vector_ids),
        }

    except Exception as exc:
        logger.error(
            "Vector deletion failed: document=%s error=%s",
            document_id, exc, exc_info=True,
        )
        raise
