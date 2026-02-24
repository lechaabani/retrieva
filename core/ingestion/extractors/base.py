"""Base extractor interface for content extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union


@dataclass
class ExtractedDocument:
    """Result of extracting content from a source file or stream."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    title: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.content or not self.content.strip()


class BaseExtractor(ABC):
    """Abstract base class for all content extractors.

    Each subclass handles a specific file format and converts it into a
    normalised ``ExtractedDocument``.
    """

    #: File extensions this extractor can handle (e.g. [".pdf"]).
    supported_extensions: list[str] = []

    @abstractmethod
    async def extract(self, source: Union[str, Path, bytes]) -> ExtractedDocument:
        """Extract text content from the given source.

        Args:
            source: A file path (str or Path) or raw bytes.

        Returns:
            An ExtractedDocument with the extracted text and metadata.

        Raises:
            ExtractionError: If extraction fails.
        """
        ...

    def can_handle(self, extension: str) -> bool:
        """Return True if this extractor supports the given file extension."""
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        return ext in self.supported_extensions
