"""Base chunker interface and Chunk data model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A single chunk of text produced by a chunking strategy."""

    content: str
    position: int
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


class BaseChunker(ABC):
    """Abstract base class for text chunking strategies.

    Subclasses split a document's text into a list of ``Chunk`` objects
    suitable for embedding and retrieval.
    """

    @abstractmethod
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split *text* into chunks.

        Args:
            text: The full document text to chunk.
            metadata: Optional metadata to propagate into each chunk.

        Returns:
            An ordered list of Chunk objects.
        """
        ...

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token count estimate (words * 1.3)."""
        return int(len(text.split()) * 1.3)
