"""OpenAI embedding provider."""

from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI

from core.exceptions import EmbeddingError
from core.ingestion.embedders.base import BaseEmbedder

logger = logging.getLogger(__name__)


class OpenAIEmbedder(BaseEmbedder):
    """Generates embeddings using the OpenAI Embeddings API.

    Defaults to the ``text-embedding-3-small`` model (1536 dimensions).
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        dimensions: Optional[int] = None,
        batch_size: int = 64,
    ) -> None:
        """
        Args:
            model: OpenAI embedding model name.
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            dimensions: Override output dimensions (supported by v3 models).
            batch_size: Maximum texts per API call.
        """
        self.model = model
        self.batch_size = batch_size
        self._client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

        # Set dimensions based on model defaults or explicit override
        if dimensions:
            self.dimensions = dimensions
        elif "3-small" in model:
            self.dimensions = 1536
        elif "3-large" in model:
            self.dimensions = 3072
        else:
            self.dimensions = 1536

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via the OpenAI API.

        Automatically batches requests to respect API limits.

        Args:
            texts: Texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: On API failure.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                # Replace empty strings to avoid API errors
                batch = [t if t.strip() else " " for t in batch]

                kwargs: dict = {"input": batch, "model": self.model}
                if self.dimensions and "3-" in self.model:
                    kwargs["dimensions"] = self.dimensions

                response = await self._client.embeddings.create(**kwargs)

                # Sort by index to guarantee order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                all_embeddings.extend([item.embedding for item in sorted_data])

            logger.debug("Embedded %d texts with OpenAI %s", len(texts), self.model)
            return all_embeddings

        except Exception as exc:
            raise EmbeddingError(f"OpenAI embedding failed: {exc}") from exc

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
