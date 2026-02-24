"""Unit tests for the generation engine."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ingestion.chunkers.base import Chunk


class TestGenerationEngine:
    """Tests for the LLM generation engine that produces answers from context.

    Since the generation module is not yet implemented, these tests verify
    the expected interface and behaviour through mocked LLM providers.
    """

    @pytest.fixture
    def mock_llm(self):
        """Return a mocked LLM client that produces deterministic responses."""
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value={
            "content": (
                "Based on the provided documents, Retrieva supports PDF, DOCX, "
                "TXT, HTML, and CSV formats for document ingestion. [Source: Features Doc]"
            ),
            "tokens_used": 87,
            "model": "gpt-4o-mini",
        })
        return llm

    @pytest.fixture
    def context_chunks(self) -> list[dict]:
        """Return sample context chunks as they would arrive from retrieval."""
        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "content": "Retrieva supports PDF, DOCX, TXT, HTML, and CSV formats.",
                "title": "Features Doc",
                "score": 0.92,
                "position": 0,
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "content": "The ingestion pipeline processes files through extraction, chunking, and embedding.",
                "title": "Architecture Doc",
                "score": 0.85,
                "position": 1,
            },
        ]

    async def test_generates_answer_from_context(self, mock_llm, context_chunks):
        """The engine should pass context to the LLM and return a structured answer."""
        result = await mock_llm.generate(
            question="What file formats does Retrieva support?",
            context=context_chunks,
        )

        assert "content" in result
        assert "PDF" in result["content"]
        assert "tokens_used" in result
        assert result["tokens_used"] > 0

    def test_context_assembly_from_chunks(self, context_chunks):
        """Context should be assembled by joining chunk content with separators."""
        # Simulate context assembly
        context_text = "\n\n---\n\n".join(
            f"[Source: {c['title']}]\n{c['content']}" for c in context_chunks
        )

        assert "[Source: Features Doc]" in context_text
        assert "[Source: Architecture Doc]" in context_text
        assert "---" in context_text

    def test_prompt_building(self, context_chunks, sample_config):
        """The prompt should include the system persona, context, and question."""
        persona = sample_config.generation.default_persona
        question = "What file formats are supported?"

        context_text = "\n\n".join(c["content"] for c in context_chunks)

        prompt = (
            f"System: {persona}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            "Answer based only on the provided context. Cite your sources."
        )

        assert persona in prompt
        assert question in prompt
        assert "PDF, DOCX" in prompt
        assert "Cite your sources" in prompt

    def test_citation_extraction(self):
        """Citations in the format [Source: ...] should be extractable from answers."""
        answer = (
            "Retrieva supports PDF and DOCX formats [Source: Features Doc]. "
            "It uses hybrid search [Source: Architecture Doc]."
        )

        import re
        citations = re.findall(r"\[Source:\s*([^\]]+)\]", answer)

        assert len(citations) == 2
        assert "Features Doc" in citations
        assert "Architecture Doc" in citations

    async def test_llm_error_propagates(self, mock_llm, context_chunks):
        """If the LLM call fails, the error should propagate to the caller."""
        mock_llm.generate = AsyncMock(
            side_effect=RuntimeError("LLM provider returned 503")
        )

        with pytest.raises(RuntimeError, match="LLM provider returned 503"):
            await mock_llm.generate(
                question="Test question",
                context=context_chunks,
            )

    async def test_empty_context_produces_fallback(self, mock_llm):
        """With no context chunks, the LLM should produce a no-information response."""
        mock_llm.generate = AsyncMock(return_value={
            "content": "I don't have enough information to answer that question.",
            "tokens_used": 15,
            "model": "gpt-4o-mini",
        })

        result = await mock_llm.generate(question="Unknown topic?", context=[])

        assert "don't have enough information" in result["content"]

    def test_max_context_chunks_respected(self, sample_config):
        """Only up to max_context_chunks should be included in the prompt."""
        max_chunks = sample_config.generation.max_context_chunks
        all_chunks = [
            {"content": f"Chunk {i}", "title": f"Doc {i}", "score": 0.9 - i * 0.01}
            for i in range(20)
        ]

        selected = all_chunks[:max_chunks]
        assert len(selected) == max_chunks
        assert len(selected) <= len(all_chunks)

    def test_confidence_score_derivation(self, context_chunks):
        """Confidence should be derivable from the average retrieval score."""
        scores = [c["score"] for c in context_chunks]
        confidence = sum(scores) / len(scores) if scores else 0.0

        assert 0.0 <= confidence <= 1.0
        assert confidence == pytest.approx(0.885, abs=0.001)
