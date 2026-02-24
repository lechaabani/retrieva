"""Integration tests for the full document ingestion flow.

These tests exercise the pipeline from file upload through extraction,
chunking, embedding, and vector storage, using mocked external services
(vector DB and embedding provider) but real chunkers and extractors.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ingestion.chunkers.base import Chunk
from core.ingestion.chunkers.fixed import FixedChunker
from core.ingestion.extractors.text import TextExtractor


@pytest.mark.integration
class TestIngestionFlow:
    """End-to-end ingestion: upload file -> extract -> chunk -> embed -> store."""

    @pytest.fixture
    def mock_vector_store_integration(self):
        """Mocked vector store that tracks upserted points."""
        store = MagicMock()
        store.upserted_points = []

        def _upsert(collection_id, points):
            store.upserted_points.extend(points)

        store.upsert = MagicMock(side_effect=_upsert)
        return store

    @pytest.fixture
    def mock_embedder_integration(self):
        """Mocked embedder producing deterministic 128-dim vectors."""
        embedder = AsyncMock()
        embedder.dimensions = 128

        async def _embed_batch(texts):
            return [[float(i) / 100.0] * 128 for i, _ in enumerate(texts)]

        embedder.embed_batch = AsyncMock(side_effect=_embed_batch)
        return embedder

    async def test_full_text_file_ingestion(
        self, temp_files, mock_vector_store_integration, mock_embedder_integration
    ):
        """Ingesting a text file should extract, chunk, embed, and store."""
        txt_path = temp_files["txt"]

        # Step 1: Extract
        extractor = TextExtractor()
        doc = await extractor.extract(txt_path)

        assert not doc.is_empty
        assert "plain text test file" in doc.content

        # Step 2: Chunk
        chunker = FixedChunker(chunk_size=50, chunk_overlap=0)
        chunks = chunker.chunk(doc.content)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.content
            assert chunk.token_count > 0

        # Step 3: Embed
        embeddings = await mock_embedder_integration.embed_batch(
            [c.content for c in chunks]
        )

        assert len(embeddings) == len(chunks)
        assert len(embeddings[0]) == 128

        # Step 4: Store in vector DB
        document_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "document_id": document_id,
                    "collection_id": collection_id,
                    "content": chunk.content,
                    "position": idx,
                    "title": doc.title,
                },
            })

        mock_vector_store_integration.upsert(collection_id, points)

        # Verify all points were stored
        assert len(mock_vector_store_integration.upserted_points) == len(chunks)
        for point in mock_vector_store_integration.upserted_points:
            assert "vector" in point
            assert "payload" in point
            assert point["payload"]["document_id"] == document_id

    async def test_html_file_ingestion(
        self, temp_files, mock_vector_store_integration, mock_embedder_integration
    ):
        """Ingesting an HTML file should strip tags before chunking."""
        from core.ingestion.extractors.html import HTMLExtractor

        html_path = temp_files["html"]

        # Extract
        extractor = HTMLExtractor()
        doc = await extractor.extract(html_path)

        assert "Hello World" in doc.content
        assert "<h1>" not in doc.content
        assert "alert" not in doc.content

        # Chunk
        chunker = FixedChunker(chunk_size=256, chunk_overlap=32)
        chunks = chunker.chunk(doc.content)

        assert len(chunks) >= 1

        # Embed
        embeddings = await mock_embedder_integration.embed_batch(
            [c.content for c in chunks]
        )

        assert len(embeddings) == len(chunks)

    async def test_csv_file_ingestion(
        self, temp_files, mock_vector_store_integration, mock_embedder_integration
    ):
        """Ingesting a CSV file should convert to pipe-delimited text."""
        csv_path = temp_files["csv"]

        extractor = TextExtractor()
        doc = await extractor.extract(csv_path)

        assert "name | age | city" in doc.content
        assert doc.metadata["source_type"] == "csv"

        chunker = FixedChunker(chunk_size=256, chunk_overlap=0)
        chunks = chunker.chunk(doc.content)

        assert len(chunks) >= 1

    async def test_empty_file_produces_no_chunks(self, tmp_path):
        """An empty file should extract empty content and produce no chunks."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        extractor = TextExtractor()
        doc = await extractor.extract(empty_file)

        assert doc.is_empty

        chunker = FixedChunker(chunk_size=256, chunk_overlap=0)
        chunks = chunker.chunk(doc.content)

        assert chunks == []

    async def test_pipeline_preserves_metadata(self, temp_files):
        """Document and chunk metadata should be preserved through the pipeline."""
        txt_path = temp_files["txt"]

        extractor = TextExtractor()
        doc = await extractor.extract(txt_path)

        assert "file_name" in doc.metadata
        assert doc.metadata["file_name"] == "sample.txt"

        chunker = FixedChunker(chunk_size=256, chunk_overlap=0)
        chunks = chunker.chunk(doc.content, metadata=doc.metadata)

        for chunk in chunks:
            assert "file_name" in chunk.metadata
            assert chunk.metadata["file_name"] == "sample.txt"
            assert chunk.metadata["chunker"] == "fixed"

    async def test_large_document_chunking(
        self, tmp_path, mock_embedder_integration
    ):
        """A large document should be split into many chunks without error."""
        large_file = tmp_path / "large.txt"
        content = "This is a sentence with enough words to count. " * 1000
        large_file.write_text(content)

        extractor = TextExtractor()
        doc = await extractor.extract(large_file)

        chunker = FixedChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(doc.content)

        assert len(chunks) > 10

        # Verify embedding works with many chunks
        embeddings = await mock_embedder_integration.embed_batch(
            [c.content for c in chunks]
        )
        assert len(embeddings) == len(chunks)
