"""Local embedding provider using sentence-transformers."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from core.exceptions import EmbeddingError
from core.ingestion.embedders.base import BaseEmbedder

logger = logging.getLogger(__name__)


class LocalEmbedder(BaseEmbedder):
    """Generates embeddings locally using sentence-transformers models.

    The model is loaded lazily on first use to avoid slow import at startup.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 64,
    ) -> None:
        """
        Args:
            model_name: HuggingFace model identifier.
            device: Torch device (e.g. "cpu", "cuda"). Auto-detected if None.
            batch_size: Batch size for encoding.
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        """Lazily load the sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device=self.device)
                self.dimensions = self._model.get_sentence_embedding_dimension()
                logger.info(
                    "Loaded local embedding model %s (dim=%d)", self.model_name, self.dimensions
                )
            except ImportError:
                raise EmbeddingError(
                    "sentence-transformers is required for LocalEmbedder. "
                    "Install it with: pip install sentence-transformers"
                )
            except Exception as exc:
                raise EmbeddingError(f"Failed to load model {self.model_name}: {exc}") from exc

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous encoding call."""
        self._load_model()
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return embeddings.tolist()
        except Exception as exc:
            raise EmbeddingError(f"Local embedding failed: {exc}") from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using the local model in a thread pool.

        Args:
            texts: Texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: On encoding failure.
        """
        if not texts:
            return []

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._encode_sync, texts)
        logger.debug("Embedded %d texts with local model %s", len(texts), self.model_name)
        return result

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
