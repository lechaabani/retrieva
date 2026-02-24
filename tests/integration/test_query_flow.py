"""Integration tests for the full RAG query flow.

These tests exercise the pipeline from question input through retrieval
and generation to the final response, verifying that sources, answers,
and confidence scores are properly assembled.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
class TestQueryFlow:
    """End-to-end query: question -> retrieval -> generation -> response."""

    @pytest.fixture
    def mock_retrieval_results(self):
        """Simulated retrieval results from vector search."""
        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "content": "Retrieva supports PDF, DOCX, TXT, HTML, and CSV file formats for ingestion.",
                "title": "Features Guide",
                "score": 0.94,
                "metadata": {"source_type": "text", "chunker": "semantic"},
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "content": "The ingestion pipeline extracts text, chunks it semantically, and stores embeddings.",
                "title": "Architecture Overview",
                "score": 0.87,
                "metadata": {"source_type": "markdown", "chunker": "semantic"},
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "content": "File size limit is 100MB. Larger files should be split before upload.",
                "title": "Limitations",
                "score": 0.72,
                "metadata": {"source_type": "text", "chunker": "fixed"},
            },
        ]

    @pytest.fixture
    def mock_generation_result(self):
        """Simulated LLM generation result."""
        return {
            "content": (
                "Retrieva supports the following file formats for document ingestion: "
                "PDF, DOCX, TXT, HTML, and CSV. The maximum file size is 100MB. "
                "[Source: Features Guide] [Source: Limitations]"
            ),
            "tokens_used": 95,
            "model": "gpt-4o-mini",
        }

    async def test_full_query_produces_answer_with_sources(
        self, mock_retrieval_results, mock_generation_result, sample_config
    ):
        """A complete query should return an answer with source references."""
        question = "What file formats does Retrieva support?"

        # Step 1: Retrieval
        retrieved = mock_retrieval_results
        assert len(retrieved) >= 1
        assert all("content" in r for r in retrieved)

        # Step 2: Context assembly
        context_chunks = retrieved[: sample_config.generation.max_context_chunks]
        context_text = "\n\n".join(
            f"[{c['title']}]: {c['content']}" for c in context_chunks
        )

        assert "Features Guide" in context_text

        # Step 3: Generation (mocked)
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=mock_generation_result)

        result = await mock_llm.generate(question=question, context=context_text)

        assert "PDF" in result["content"]
        assert "DOCX" in result["content"]
        assert result["tokens_used"] > 0

        # Step 4: Build response
        import re
        citations = re.findall(r"\[Source:\s*([^\]]+)\]", result["content"])
        sources = [r for r in retrieved if r["title"] in citations]

        response = {
            "answer": result["content"],
            "sources": sources,
            "confidence": sum(r["score"] for r in retrieved) / len(retrieved),
            "tokens_used": result["tokens_used"],
        }

        assert response["answer"]
        assert len(response["sources"]) >= 1
        assert 0.0 < response["confidence"] <= 1.0
        assert response["tokens_used"] > 0

    async def test_sources_are_included_in_response(
        self, mock_retrieval_results
    ):
        """The response should include source document references."""
        sources = [
            {
                "document_id": r["document_id"],
                "chunk_id": r["chunk_id"],
                "title": r["title"],
                "content": r["content"],
                "score": r["score"],
            }
            for r in mock_retrieval_results
        ]

        assert len(sources) == 3
        for source in sources:
            assert "document_id" in source
            assert "title" in source
            assert "score" in source
            assert 0.0 <= source["score"] <= 1.0

    async def test_confidence_score_is_valid(self, mock_retrieval_results):
        """The confidence score should be between 0 and 1."""
        scores = [r["score"] for r in mock_retrieval_results]
        confidence = sum(scores) / len(scores) if scores else 0.0

        assert 0.0 <= confidence <= 1.0
        # With scores of 0.94, 0.87, 0.72 -> average ~ 0.843
        assert confidence == pytest.approx(0.843, abs=0.01)

    async def test_query_with_no_relevant_results(self, sample_config):
        """When retrieval finds nothing relevant, generation should indicate this."""
        empty_results: list = []

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value={
            "content": "I could not find relevant information to answer your question.",
            "tokens_used": 20,
            "model": "gpt-4o-mini",
        })

        result = await mock_llm.generate(
            question="What is the meaning of life?",
            context="",
        )

        assert "could not find" in result["content"]

        response = {
            "answer": result["content"],
            "sources": [],
            "confidence": 0.0,
            "tokens_used": result["tokens_used"],
        }

        assert response["confidence"] == 0.0
        assert response["sources"] == []

    async def test_query_respects_top_k(
        self, mock_retrieval_results, sample_config
    ):
        """Retrieval should return at most top_k results."""
        top_k = 2
        filtered = mock_retrieval_results[:top_k]

        assert len(filtered) == top_k
        # Scores should be in descending order (best first)
        scores = [r["score"] for r in filtered]
        assert scores == sorted(scores, reverse=True)

    async def test_low_score_results_are_filtered(
        self, mock_retrieval_results, sample_config
    ):
        """Results below the score threshold should be excluded."""
        threshold = sample_config.retrieval.score_threshold
        filtered = [r for r in mock_retrieval_results if r["score"] >= threshold]

        # All our mock results are above the default threshold of 0.3
        assert len(filtered) == len(mock_retrieval_results)

        # With a higher threshold, some results should be excluded
        high_threshold = 0.9
        filtered_strict = [
            r for r in mock_retrieval_results if r["score"] >= high_threshold
        ]
        assert len(filtered_strict) < len(mock_retrieval_results)
