"""Semantic chunker that respects paragraph and sentence boundaries."""

from __future__ import annotations

import logging
import re
from typing import Any

from core.ingestion.chunkers.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n")


class SemanticChunker(BaseChunker):
    """Splits text into semantically coherent chunks.

    The strategy groups paragraphs together up to a target token budget,
    and avoids splitting sentences across chunk boundaries.
    """

    def __init__(self, max_chunk_tokens: int = 512, min_chunk_tokens: int = 50) -> None:
        """
        Args:
            max_chunk_tokens: Maximum token count per chunk.
            min_chunk_tokens: Minimum token count before starting a new chunk.
        """
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        if not text or not text.strip():
            return []

        meta = metadata or {}
        paragraphs = _PARAGRAPH_BOUNDARY.split(text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        position = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)

            # If single paragraph exceeds budget, split by sentences
            if para_tokens > self.max_chunk_tokens:
                # Flush any accumulated text first
                if current_parts:
                    chunks.append(self._make_chunk(current_parts, position, meta))
                    position += 1
                    current_parts = []
                    current_tokens = 0

                sentence_chunks = self._split_paragraph_by_sentences(para, meta, position)
                chunks.extend(sentence_chunks)
                position += len(sentence_chunks)
                continue

            # Check if adding this paragraph would exceed budget
            if current_tokens + para_tokens > self.max_chunk_tokens and current_tokens >= self.min_chunk_tokens:
                chunks.append(self._make_chunk(current_parts, position, meta))
                position += 1
                current_parts = []
                current_tokens = 0

            current_parts.append(para)
            current_tokens += para_tokens

        # Flush remainder
        if current_parts:
            chunks.append(self._make_chunk(current_parts, position, meta))

        logger.debug("SemanticChunker produced %d chunks", len(chunks))
        return chunks

    def _make_chunk(self, parts: list[str], position: int, meta: dict[str, Any]) -> Chunk:
        content = "\n\n".join(parts)
        return Chunk(
            content=content,
            position=position,
            metadata={**meta, "chunker": "semantic"},
            token_count=self._estimate_tokens(content),
        )

    def _split_paragraph_by_sentences(
        self, paragraph: str, meta: dict[str, Any], start_position: int
    ) -> list[Chunk]:
        """Split a long paragraph at sentence boundaries."""
        sentences = _SENTENCE_BOUNDARY.split(paragraph)
        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        position = start_position

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sent_tokens = self._estimate_tokens(sentence)

            if current_tokens + sent_tokens > self.max_chunk_tokens and current_parts:
                content = " ".join(current_parts)
                chunks.append(
                    Chunk(
                        content=content,
                        position=position,
                        metadata={**meta, "chunker": "semantic"},
                        token_count=self._estimate_tokens(content),
                    )
                )
                position += 1
                current_parts = []
                current_tokens = 0

            current_parts.append(sentence)
            current_tokens += sent_tokens

        if current_parts:
            content = " ".join(current_parts)
            chunks.append(
                Chunk(
                    content=content,
                    position=position,
                    metadata={**meta, "chunker": "semantic"},
                    token_count=self._estimate_tokens(content),
                )
            )

        return chunks
