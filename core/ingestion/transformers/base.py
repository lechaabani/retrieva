"""Base transformer interface for the enrichment pipeline phase."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTransformer(ABC):
    """Abstract base class for content transformers.

    Transformers receive text and metadata, apply a transformation, and
    return the (possibly modified) text and metadata.  They are applied
    sequentially between the ``clean`` and ``chunk`` stages of the
    ingestion pipeline.
    """

    #: Human-readable transformer name.
    name: str = "base"

    @abstractmethod
    def transform(
        self, text: str, metadata: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Transform the text and/or metadata.

        Args:
            text: The cleaned document text.
            metadata: Mutable metadata dict associated with the document.

        Returns:
            A tuple of ``(transformed_text, transformed_metadata)``.
            Returning ``None`` as the text signals that the document
            should be skipped (e.g. duplicate detection).
        """
        ...
