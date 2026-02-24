"""Cohere embedding provider (placeholder)."""

from __future__ import annotations

from core.exceptions import EmbeddingError
from core.ingestion.embedders.base import BaseEmbedder


class CohereEmbedder(BaseEmbedder):
    """Placeholder for Cohere embedding integration.

    This embedder will use Cohere's embed-english-v3.0 model once implemented.
    """

    def __init__(self, model: str = "embed-english-v3.0", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key
        self.dimensions = 1024

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingError(
            "CohereEmbedder is not yet implemented. "
            "Install cohere and implement the API integration."
        )

    async def embed_query(self, text: str) -> list[float]:
        raise EmbeddingError("CohereEmbedder is not yet implemented.")
