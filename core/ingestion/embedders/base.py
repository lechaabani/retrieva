"""Base embedder interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Abstract base class for text embedding providers.

    Subclasses convert text strings into dense vector representations
    suitable for similarity search.
    """

    #: Dimensionality of the output vectors.
    dimensions: int = 0

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            A list of embedding vectors, one per input text.

        Raises:
            EmbeddingError: If the embedding call fails.
        """
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Some providers use a different model or prefix for queries vs. documents.
        The default implementation delegates to ``embed``.

        Args:
            text: The query text.

        Returns:
            A single embedding vector.
        """
        results = await self.embed([text])
        return results[0]
