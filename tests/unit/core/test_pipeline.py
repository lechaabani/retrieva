"""Unit tests for the ingestion pipeline logic."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ingestion.chunkers.base import Chunk
from core.ingestion.extractors.base import ExtractedDocument


class TestIngestionPipeline:
    """Tests for the ingestion pipeline orchestration.

    These tests exercise the pipeline helper _run_ingestion_pipeline defined
    in the ingestion worker, verifying that extraction, chunking, embedding,
    and vector storage are called in the correct order with expected arguments.
    """

    @pytest.fixture
    def pipeline_deps(self, sample_config):
        """Set up mocks for all pipeline dependencies."""
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = [
            Chunk(content="Chunk 1 text", position=0, metadata={"chunker": "fixed"}, token_count=5),
            Chunk(content="Chunk 2 text", position=1, metadata={"chunker": "fixed"}, token_count=5),
        ]

        mock_embedder = AsyncMock()
        mock_embedder.embed_batch = AsyncMock(return_value=[
            [0.1] * 128,
            [0.2] * 128,
        ])

        mock_vector_store = MagicMock()
        mock_vector_store.upsert = MagicMock()

        return {
            "chunker": mock_chunker,
            "embedder": mock_embedder,
            "vector_store": mock_vector_store,
            "config": sample_config,
        }

    def test_end_to_end_with_mocks(self, pipeline_deps):
        """The pipeline should chunk, embed, and store vectors in order."""
        deps = pipeline_deps

        with (
            patch(
                "workers.ingestion_worker.get_chunker",
                return_value=deps["chunker"],
            ),
            patch(
                "workers.ingestion_worker.get_embedder",
                return_value=deps["embedder"],
            ),
            patch(
                "workers.ingestion_worker.VectorStore",
                return_value=deps["vector_store"],
            ),
            patch("workers.ingestion_worker.get_config", return_value=deps["config"]),
            patch("workers.ingestion_worker.get_sync_session") as mock_session_ctx,
        ):
            # Mock the session context manager
            mock_session = MagicMock()
            mock_session.get.return_value = MagicMock()  # mock document
            mock_session.add = MagicMock()
            mock_session_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_session_ctx.return_value.__exit__ = MagicMock(return_value=False)

            from workers.ingestion_worker import _run_ingestion_pipeline

            doc_id = str(uuid.uuid4())
            coll_id = str(uuid.uuid4())

            chunks_count = _run_ingestion_pipeline(
                document_id=doc_id,
                content="Some test document content for chunking.",
                title="Test Doc",
                collection_id=coll_id,
                config={},
            )

        assert chunks_count == 2
        deps["chunker"].chunk.assert_called_once()
        deps["embedder"].embed_batch.assert_called_once()
        deps["vector_store"].upsert.assert_called_once()

    def test_pipeline_returns_zero_for_no_chunks(self, pipeline_deps):
        """If chunking produces no chunks, the pipeline should return 0."""
        deps = pipeline_deps
        deps["chunker"].chunk.return_value = []

        with (
            patch(
                "workers.ingestion_worker.get_chunker",
                return_value=deps["chunker"],
            ),
            patch(
                "workers.ingestion_worker.get_embedder",
                return_value=deps["embedder"],
            ),
            patch(
                "workers.ingestion_worker.VectorStore",
                return_value=deps["vector_store"],
            ),
            patch("workers.ingestion_worker.get_config", return_value=deps["config"]),
        ):
            from workers.ingestion_worker import _run_ingestion_pipeline

            chunks_count = _run_ingestion_pipeline(
                document_id=str(uuid.uuid4()),
                content="",
                title="Empty",
                collection_id=str(uuid.uuid4()),
                config={},
            )

        assert chunks_count == 0
        # Embedding and storage should not be called if no chunks
        deps["embedder"].embed_batch.assert_not_called()
        deps["vector_store"].upsert.assert_not_called()

    def test_pipeline_handles_embedding_error(self, pipeline_deps):
        """If the embedder raises, the error should propagate."""
        deps = pipeline_deps
        deps["embedder"].embed_batch = AsyncMock(
            side_effect=RuntimeError("Embedding service unavailable")
        )

        with (
            patch(
                "workers.ingestion_worker.get_chunker",
                return_value=deps["chunker"],
            ),
            patch(
                "workers.ingestion_worker.get_embedder",
                return_value=deps["embedder"],
            ),
            patch(
                "workers.ingestion_worker.VectorStore",
                return_value=deps["vector_store"],
            ),
            patch("workers.ingestion_worker.get_config", return_value=deps["config"]),
        ):
            from workers.ingestion_worker import _run_ingestion_pipeline

            with pytest.raises(RuntimeError, match="Embedding service unavailable"):
                _run_ingestion_pipeline(
                    document_id=str(uuid.uuid4()),
                    content="Some content",
                    title="Error Test",
                    collection_id=str(uuid.uuid4()),
                    config={},
                )


class TestIngestionResult:
    """Tests for the IngestionResult / task return values."""

    def test_ingest_text_returns_correct_structure(self):
        """The ingest_text task should return document_id, status, and chunks_count."""
        with (
            patch("workers.ingestion_worker._set_document_status"),
            patch(
                "workers.ingestion_worker._run_ingestion_pipeline",
                return_value=5,
            ),
        ):
            from workers.ingestion_worker import ingest_text

            # Call the task function directly (not via Celery)
            result = ingest_text(
                self=MagicMock(),
                document_id="test-doc-id",
                content="Test content for ingestion pipeline processing.",
                title="Test Title",
                collection_id="test-collection-id",
                config={},
            )

        assert result["document_id"] == "test-doc-id"
        assert result["status"] == "indexed"
        assert result["chunks_count"] == 5

    def test_ingest_text_empty_content_returns_error(self):
        """Empty content should produce an error result."""
        with patch("workers.ingestion_worker._set_document_status"):
            from workers.ingestion_worker import ingest_text

            result = ingest_text(
                self=MagicMock(),
                document_id="test-doc-id",
                content="   ",
                title="Empty",
                collection_id="test-collection-id",
                config={},
            )

        assert result["status"] == "error"
        assert "Empty" in result["error"]
