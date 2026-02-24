"""Cross-encoder reranker for improving retrieval precision."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from core.exceptions import RetrievalError
from core.retrieval.engine import ScoredChunk

logger = logging.getLogger(__name__)


class Reranker:
    """Reranks retrieved chunks using a cross-encoder model.

    Uses sentence-transformers CrossEncoder to compute query-document
    relevance scores, providing more accurate ranking than bi-encoder
    similarity alone.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: Optional[str] = None,
    ) -> None:
        """
        Args:
            model_name: HuggingFace cross-encoder model identifier.
            device: Torch device. Auto-detected if None.
        """
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load_model(self):
        """Lazily load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.model_name, device=self.device)
                logger.info("Loaded cross-encoder model: %s", self.model_name)
            except ImportError:
                raise RetrievalError(
                    "sentence-transformers is required for Reranker. "
                    "Install it with: pip install sentence-transformers"
                )
            except Exception as exc:
                raise RetrievalError(f"Failed to load reranker model: {exc}") from exc

    def _rerank_sync(
        self, query: str, chunks: list[ScoredChunk], top_k: int
    ) -> list[ScoredChunk]:
        """Synchronous reranking."""
        self._load_model()

        if not chunks:
            return []

        pairs = [[query, chunk.content] for chunk in chunks]
        try:
            scores = self._model.predict(pairs)
        except Exception as exc:
            raise RetrievalError(f"Reranking prediction failed: {exc}") from exc

        # Attach new scores
        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
        return ranked[:top_k]

    async def rerank(
        self, query: str, chunks: list[ScoredChunk], top_k: int = 5
    ) -> list[ScoredChunk]:
        """Rerank chunks by cross-encoder relevance to the query.

        Args:
            query: The user query.
            chunks: Candidate chunks from initial retrieval.
            top_k: Number of top results to return.

        Returns:
            Reranked list of ScoredChunk, truncated to top_k.

        Raises:
            RetrievalError: On model loading or prediction failure.
        """
        if not chunks:
            return []

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._rerank_sync, query, chunks, top_k)
        logger.debug("Reranked %d chunks -> top %d", len(chunks), top_k)
        return result
