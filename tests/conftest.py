"""Shared pytest fixtures for the Retrieva test suite.

Provides reusable fixtures for database sessions, HTTP clients,
configuration, mocks, and sample data objects.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Environment overrides (must be set before importing application modules)
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "30")

from api.database import Base  # noqa: E402
from api.models.api_key import ApiKey  # noqa: E402
from api.models.chunk import Chunk as ChunkModel  # noqa: E402
from api.models.collection import Collection  # noqa: E402
from api.models.document import Document, DocumentStatus  # noqa: E402
from api.models.tenant import Tenant  # noqa: E402
from api.models.user import User  # noqa: E402
from core.config import (  # noqa: E402
    IngestionConfig,
    PlatformConfig,
    RetrievalConfig,
    GenerationConfig,
)
from core.ingestion.chunkers.base import Chunk  # noqa: E402
from core.ingestion.extractors.base import ExtractedDocument  # noqa: E402


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async SQLAlchemy session bound to the in-memory database."""
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_client(async_engine, async_session) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the FastAPI app with overridden DB.

    The database dependency is replaced with the test async_session so that
    all requests hit the in-memory SQLite database.
    """
    from api.database import get_db

    # Late import to avoid circular issues and to let env vars take effect.
    try:
        from api.main import app
    except ImportError:
        # If api.main does not exist yet, build a minimal app for testing.
        from fastapi import FastAPI
        app = FastAPI()

    async def _override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Configuration fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_config() -> PlatformConfig:
    """Return a PlatformConfig instance with sensible test defaults."""
    return PlatformConfig(
        app_name="Retrieva Test",
        environment="test",
        debug=True,
        log_level="DEBUG",
        ingestion=IngestionConfig(
            default_chunking_strategy="fixed",
            default_chunk_size=256,
            chunk_overlap=32,
            default_embedding_model="test-model",
            embedding_provider="openai",
            embedding_dimensions=128,
        ),
        retrieval=RetrievalConfig(
            default_strategy="hybrid",
            default_top_k=5,
            rerank_enabled=False,
        ),
        generation=GenerationConfig(
            default_provider="openai",
            default_model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=512,
        ),
    )


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Return a mocked VectorStore with common methods stubbed."""
    store = MagicMock()
    store.upsert = MagicMock(return_value=None)
    store.search = MagicMock(return_value=[])
    store.delete = MagicMock(return_value=None)
    store.collection_exists = MagicMock(return_value=True)
    store.create_collection = MagicMock(return_value=None)
    return store


@pytest.fixture
def mock_embedder() -> AsyncMock:
    """Return a mocked embedder that produces random 128-dim vectors."""
    import random

    embedder = AsyncMock()
    embedder.dimensions = 128

    async def _embed(texts: list[str]) -> list[list[float]]:
        return [[random.uniform(-1, 1) for _ in range(128)] for _ in texts]

    async def _embed_query(text: str) -> list[float]:
        return [random.uniform(-1, 1) for _ in range(128)]

    embedder.embed = AsyncMock(side_effect=_embed)
    embedder.embed_query = AsyncMock(side_effect=_embed_query)
    return embedder


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Return a fixed tenant UUID for tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def collection_id() -> uuid.UUID:
    """Return a fixed collection UUID for tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000010")


@pytest.fixture
def document_id() -> uuid.UUID:
    """Return a fixed document UUID for tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000100")


@pytest.fixture
def sample_document(tenant_id, collection_id, document_id) -> dict[str, Any]:
    """Return a dictionary representing a sample Document row."""
    return {
        "id": document_id,
        "collection_id": collection_id,
        "source_connector": "file_upload",
        "source_id": None,
        "title": "Test Document",
        "content_hash": "abc123",
        "metadata": {"source_type": "text", "file_name": "test.txt"},
        "status": "indexed",
        "chunks_count": 3,
        "indexed_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_chunks(document_id, collection_id) -> list[Chunk]:
    """Return a list of sample Chunk dataclass instances."""
    texts = [
        "Retrieva is a RAG platform designed for enterprise document search.",
        "The ingestion pipeline supports PDF, DOCX, TXT, HTML, and CSV formats.",
        "Hybrid retrieval combines vector similarity with keyword matching.",
    ]
    return [
        Chunk(
            content=text,
            position=idx,
            metadata={"chunker": "fixed", "document_id": str(document_id)},
            token_count=len(text.split()),
        )
        for idx, text in enumerate(texts)
    ]


@pytest.fixture
def sample_extracted_document() -> ExtractedDocument:
    """Return a sample ExtractedDocument from the extraction phase."""
    return ExtractedDocument(
        content=(
            "Retrieva is a configurable RAG platform.\n\n"
            "It supports multiple file formats and data sources.\n\n"
            "The retrieval engine uses hybrid search combining vector "
            "similarity with BM25 keyword matching."
        ),
        metadata={"source_type": "text", "file_name": "test.txt", "char_count": 200},
        title="Test Document",
    )


# ---------------------------------------------------------------------------
# Temporary file fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_files(tmp_path) -> dict[str, Path]:
    """Create temporary test files for extractor tests.

    Returns a dict mapping format names to file paths.
    """
    files: dict[str, Path] = {}

    # Plain text
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text(
        "This is a plain text test file.\nIt has multiple lines.\nUsed for testing.",
        encoding="utf-8",
    )
    files["txt"] = txt_file

    # Markdown
    md_file = tmp_path / "sample.md"
    md_file.write_text(
        "# Test Heading\n\nThis is a **markdown** file.\n\n## Section 2\n\nMore content here.",
        encoding="utf-8",
    )
    files["md"] = md_file

    # CSV
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "name,age,city\nAlice,30,Paris\nBob,25,London\nCharlie,35,Berlin",
        encoding="utf-8",
    )
    files["csv"] = csv_file

    # HTML
    html_file = tmp_path / "sample.html"
    html_file.write_text(
        "<!DOCTYPE html>\n<html>\n<head><title>Test Page</title></head>\n"
        "<body>\n<h1>Hello World</h1>\n<p>This is test HTML content.</p>\n"
        "<script>alert('ignored');</script>\n"
        "<nav>Navigation content</nav>\n"
        "</body>\n</html>",
        encoding="utf-8",
    )
    files["html"] = html_file

    # Simulated PDF bytes (for byte-based extraction testing)
    pdf_bytes_file = tmp_path / "sample_bytes.bin"
    pdf_bytes_file.write_bytes(b"fake pdf bytes for mocking")
    files["pdf_bytes"] = pdf_bytes_file

    return files
