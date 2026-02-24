"""Fixed-size chunker that splits text by approximate token count with overlap."""

from __future__ import annotations

import logging
from typing import Any

from core.ingestion.chunkers.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)


class FixedChunker(BaseChunker):
    """Splits text into fixed-size chunks by approximate token count.

    Uses word boundaries so chunks do not cut words in half. An overlap
    window is applied between consecutive chunks to preserve context.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        """
        Args:
            chunk_size: Target token count per chunk.
            chunk_overlap: Number of overlapping tokens between consecutive chunks.
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        if not text or not text.strip():
            return []

        meta = metadata or {}
        words = text.split()

        # Approximate words per chunk (tokens ~ words * 1.3)
        words_per_chunk = max(1, int(self.chunk_size / 1.3))
        overlap_words = max(0, int(self.chunk_overlap / 1.3))
        step = max(1, words_per_chunk - overlap_words)

        chunks: list[Chunk] = []
        position = 0
        start = 0

        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk_text = " ".join(words[start:end])

            chunks.append(
                Chunk(
                    content=chunk_text,
                    position=position,
                    metadata={**meta, "chunker": "fixed"},
                    token_count=self._estimate_tokens(chunk_text),
                )
            )
            position += 1
            start += step

            # Avoid duplicate trailing chunk
            if end >= len(words):
                break

        logger.debug("FixedChunker produced %d chunks", len(chunks))
        return chunks
