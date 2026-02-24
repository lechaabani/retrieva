"""Document-level chunker that treats the entire document as a single chunk."""

from __future__ import annotations

import logging
from typing import Any

from core.ingestion.chunkers.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)


class DocumentChunker(BaseChunker):
    """Produces a single chunk containing the entire document text.

    Useful for short documents or when full-document embeddings are desired.
    """

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        if not text or not text.strip():
            return []

        meta = metadata or {}
        content = text.strip()

        chunk = Chunk(
            content=content,
            position=0,
            metadata={**meta, "chunker": "document"},
            token_count=self._estimate_tokens(content),
        )

        logger.debug("DocumentChunker produced 1 chunk (%d tokens)", chunk.token_count)
        return [chunk]
