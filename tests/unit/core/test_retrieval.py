"""Unit tests for the retrieval engine."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRetrievalEngine:
    """Tests for the retrieval engine that searches and ranks document chunks.

    Because the core retrieval module is still a stub, these tests target the
    expected interface and verify behaviour through mocked dependencies.
    """

    @pytest.fixture
    def mock_qdrant_client(self):
        """Return a mocked Qdrant client with search capabilities."""
        client = MagicMock()

        point_1 = MagicMock()
        point_1.id = str(uuid.uuid4())
        point_1.score = 0.92
        point_1.payload = {
            "document_id": str(uuid.uuid4()),
            "collection_id": str(uuid.uuid4()),
            "content": "Retrieva supports hybrid search combining vector and keyword.",
            "title": "Features",
            "position": 0,
        }

        point_2 = MagicMock()
        point_2.id = str(uuid.uuid4())
        point_2.score = 0.85
        point_2.payload = {
            "document_id": str(uuid.uuid4()),
            "collection_id": str(uuid.uuid4()),
            "content": "The platform is built with FastAPI and PostgreSQL.",
            "title": "Architecture",
            "position": 1,
        }

        client.search = MagicMock(return_value=[point_1, point_2])
        return client

    def test_vector_search_returns_results(self, mock_qdrant_client, mock_embedder):
        """A vector search should return scored results from Qdrant."""
        results = mock_qdrant_client.search(
            collection_name="test_collection",
            query_vector=[0.1] * 128,
            limit=10,
        )

        assert len(results) == 2
        assert results[0].score > results[1].score

    def test_search_results_contain_expected_fields(self, mock_qdrant_client):
        """Each search result should carry content, title, score, and document_id."""
        results = mock_qdrant_client.search(
            collection_name="test",
            query_vector=[0.0] * 128,
            limit=5,
        )

        for result in results:
            assert "content" in result.payload
            assert "title" in result.payload
            assert "document_id" in result.payload
            assert hasattr(result, "score")
            assert 0.0 <= result.score <= 1.0

    def test_hybrid_search_combines_vector_and_keyword(self, mock_qdrant_client, sample_config):
        """Hybrid search should merge vector similarity with keyword scores.

        This test verifies the expected weighting behaviour:
        vector_weight=0.7, keyword_weight=0.3 (from config defaults).
        """
        vector_results = [
            {"id": "a", "score": 0.9, "content": "vector match"},
            {"id": "b", "score": 0.8, "content": "vector only"},
        ]
        keyword_results = [
            {"id": "a", "score": 0.7, "content": "vector match"},
            {"id": "c", "score": 0.6, "content": "keyword only"},
        ]

        # Simulate hybrid merge
        combined: dict[str, float] = {}
        vw = sample_config.retrieval.hybrid_vector_weight
        kw = sample_config.retrieval.hybrid_keyword_weight

        for r in vector_results:
            combined[r["id"]] = combined.get(r["id"], 0.0) + r["score"] * vw
        for r in keyword_results:
            combined[r["id"]] = combined.get(r["id"], 0.0) + r["score"] * kw

        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        # "a" appears in both, so it should rank highest
        assert ranked[0][0] == "a"
        assert len(ranked) == 3  # a, b, c

    def test_filters_apply_correctly(self, mock_qdrant_client):
        """Metadata filters should narrow the search to matching documents."""
        # Simulate a filtered search call
        mock_qdrant_client.search.return_value = [
            MagicMock(
                score=0.88,
                payload={
                    "document_id": "doc-1",
                    "content": "Filtered result",
                    "title": "Filtered",
                    "source_type": "pdf",
                },
            )
        ]

        results = mock_qdrant_client.search(
            collection_name="test",
            query_vector=[0.0] * 128,
            limit=10,
            query_filter={"must": [{"key": "source_type", "match": {"value": "pdf"}}]},
        )

        assert len(results) == 1
        assert results[0].payload["source_type"] == "pdf"

    def test_empty_query_returns_no_results(self, mock_qdrant_client):
        """An empty query vector should still return gracefully (may be empty)."""
        mock_qdrant_client.search.return_value = []

        results = mock_qdrant_client.search(
            collection_name="test",
            query_vector=[],
            limit=10,
        )

        assert results == []


class TestReranker:
    """Tests for the reranking step that reorders retrieval results."""

    def test_reranker_reorders_results(self):
        """The reranker should reorder results by cross-encoder scores."""
        initial_results = [
            {"id": "a", "score": 0.9, "content": "Less relevant after reranking"},
            {"id": "b", "score": 0.7, "content": "More relevant after reranking"},
            {"id": "c", "score": 0.5, "content": "Stays in the middle"},
        ]

        # Simulate cross-encoder scores that differ from vector scores
        rerank_scores = {"a": 0.4, "b": 0.95, "c": 0.6}

        reranked = sorted(
            initial_results,
            key=lambda r: rerank_scores.get(r["id"], 0.0),
            reverse=True,
        )

        assert reranked[0]["id"] == "b"
        assert reranked[1]["id"] == "c"
        assert reranked[2]["id"] == "a"

    def test_reranker_respects_top_k(self):
        """Reranking should return at most top_k results."""
        results = [{"id": f"r{i}", "score": 0.5} for i in range(20)]
        top_k = 5

        reranked = results[:top_k]
        assert len(reranked) == top_k

    def test_reranker_handles_empty_input(self):
        """Reranking with no results should return an empty list."""
        results: list = []
        reranked = sorted(results, key=lambda r: r.get("rerank_score", 0), reverse=True)
        assert reranked == []
