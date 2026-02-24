"""Unit tests for text chunking strategies."""

from __future__ import annotations

import pytest

from core.ingestion.chunkers.base import Chunk
from core.ingestion.chunkers.document import DocumentChunker
from core.ingestion.chunkers.fixed import FixedChunker
from core.ingestion.chunkers.semantic import SemanticChunker


# =============================================================================
# FixedChunker
# =============================================================================

class TestFixedChunker:
    """Tests for the fixed-size chunking strategy."""

    def test_chunks_text_at_correct_size(self):
        """Chunks should approximate the target token count."""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=0)
        # ~100 words -> should produce multiple chunks
        text = " ".join(["word"] * 100)
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        for chunk in chunks:
            # Each chunk should not vastly exceed the target
            word_count = len(chunk.content.split())
            assert word_count <= int(50 / 1.3) + 5  # allow small margin

    def test_respects_overlap(self):
        """Consecutive chunks should share overlapping words."""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=20)
        words = [f"w{i}" for i in range(100)]
        text = " ".join(words)
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        # Verify the second chunk starts before the first chunk ends
        first_words = set(chunks[0].content.split())
        second_words = set(chunks[1].content.split())
        overlap = first_words & second_words
        assert len(overlap) > 0, "Expected overlapping words between consecutive chunks"

    def test_handles_short_text(self):
        """Short text that fits in one chunk should produce exactly one chunk."""
        chunker = FixedChunker(chunk_size=512, chunk_overlap=64)
        text = "This is a very short document."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].position == 0

    def test_empty_text_returns_empty(self):
        """Empty or whitespace-only text should produce no chunks."""
        chunker = FixedChunker(chunk_size=512, chunk_overlap=64)

        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []
        assert chunker.chunk("\n\n") == []

    def test_metadata_propagation(self):
        """Metadata passed to chunk() should appear on every chunk."""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=0)
        text = " ".join(["hello"] * 100)
        meta = {"doc_id": "123", "source": "test"}
        chunks = chunker.chunk(text, metadata=meta)

        for chunk in chunks:
            assert chunk.metadata["doc_id"] == "123"
            assert chunk.metadata["source"] == "test"
            assert chunk.metadata["chunker"] == "fixed"

    def test_positions_are_sequential(self):
        """Chunk positions should be sequential integers starting at 0."""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=0)
        text = " ".join(["word"] * 200)
        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.position == i

    def test_overlap_must_be_less_than_size(self):
        """Overlap >= chunk_size should raise ValueError."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            FixedChunker(chunk_size=100, chunk_overlap=100)

        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            FixedChunker(chunk_size=100, chunk_overlap=200)

    def test_token_count_is_set(self):
        """Each chunk should have a non-zero token_count estimate."""
        chunker = FixedChunker(chunk_size=512, chunk_overlap=64)
        text = "This is a test document with several words in it."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].token_count > 0


# =============================================================================
# SemanticChunker
# =============================================================================

class TestSemanticChunker:
    """Tests for the semantic (paragraph-boundary) chunking strategy."""

    def test_splits_on_paragraphs(self):
        """Distinct paragraphs should result in separate chunks when budget allows."""
        chunker = SemanticChunker(max_chunk_tokens=30, min_chunk_tokens=5)
        text = (
            "First paragraph with enough content to stand alone.\n\n"
            "Second paragraph that is also long enough on its own.\n\n"
            "Third paragraph concluding the document content here."
        )
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.metadata["chunker"] == "semantic"

    def test_respects_max_size(self):
        """No chunk should exceed the max token budget by a large margin."""
        chunker = SemanticChunker(max_chunk_tokens=50, min_chunk_tokens=10)
        paragraphs = [f"Paragraph {i} " + " ".join(["filler"] * 20) for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunker.chunk(text)

        for chunk in chunks:
            # Allow some tolerance since the estimate is approximate
            assert chunk.token_count <= 80, (
                f"Chunk exceeded expected max: {chunk.token_count} tokens"
            )

    def test_merges_small_paragraphs(self):
        """Small paragraphs should be merged into a single chunk if under budget."""
        chunker = SemanticChunker(max_chunk_tokens=500, min_chunk_tokens=10)
        text = "Short one.\n\nShort two.\n\nShort three."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert "Short one." in chunks[0].content
        assert "Short three." in chunks[0].content

    def test_empty_text_returns_empty(self):
        """Empty text should produce no chunks."""
        chunker = SemanticChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("  \n\n  ") == []

    def test_single_paragraph(self):
        """A single paragraph should produce exactly one chunk."""
        chunker = SemanticChunker(max_chunk_tokens=500)
        text = "This is a single paragraph without any double newlines."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_long_paragraph_splits_by_sentences(self):
        """A paragraph that exceeds max tokens should be split at sentence boundaries."""
        chunker = SemanticChunker(max_chunk_tokens=30, min_chunk_tokens=5)
        # Build a single paragraph with many sentences
        sentences = [f"Sentence number {i} has enough words to count." for i in range(20)]
        text = " ".join(sentences)  # no paragraph breaks
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2


# =============================================================================
# DocumentChunker
# =============================================================================

class TestDocumentChunker:
    """Tests for the whole-document chunking strategy."""

    def test_single_chunk_output(self):
        """The entire document should be emitted as a single chunk."""
        chunker = DocumentChunker()
        text = "Full document text that should remain as one piece."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].position == 0
        assert chunks[0].metadata["chunker"] == "document"

    def test_strips_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        chunker = DocumentChunker()
        text = "  \n  Content with whitespace  \n  "
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == "Content with whitespace"

    def test_empty_text_returns_empty(self):
        """Empty text should produce no chunks."""
        chunker = DocumentChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_metadata_propagation(self):
        """Metadata should be passed through to the chunk."""
        chunker = DocumentChunker()
        meta = {"doc_id": "456"}
        chunks = chunker.chunk("Some content", metadata=meta)

        assert chunks[0].metadata["doc_id"] == "456"
        assert chunks[0].metadata["chunker"] == "document"

    def test_token_count_estimated(self):
        """The single chunk should have a token count estimate."""
        chunker = DocumentChunker()
        text = "Word " * 50
        chunks = chunker.chunk(text)

        assert chunks[0].token_count > 0
