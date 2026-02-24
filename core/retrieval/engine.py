"""Retrieval engine supporting vector, keyword, and hybrid search strategies."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from core.exceptions import RetrievalError
from core.ingestion.embedders.base import BaseEmbedder

logger = logging.getLogger(__name__)


class SearchStrategy(str, Enum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class ScoredChunk:
    """A retrieved chunk with its relevance score."""

    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str = ""


@dataclass
class RetrievalResult:
    """Result of a retrieval search."""

    chunks: list[ScoredChunk]
    strategy: str
    total_candidates: int = 0
    query: str = ""


@dataclass
class SearchOptions:
    """Options controlling retrieval behaviour."""

    strategy: SearchStrategy = SearchStrategy.HYBRID
    top_k: int = 10
    score_threshold: float = 0.0
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    filters: dict[str, Any] | None = None


class RetrievalEngine:
    """Unified search engine combining vector and keyword retrieval.

    Supports three strategies:
    - **vector**: semantic similarity via Qdrant.
    - **keyword**: lexical matching via BM25.
    - **hybrid**: weighted combination of both.
    """

    def __init__(
        self,
        vector_store: Any,
        embedder: BaseEmbedder,
        default_top_k: int = 10,
        default_strategy: str = "hybrid",
        hybrid_vector_weight: float = 0.7,
        hybrid_keyword_weight: float = 0.3,
    ) -> None:
        """
        Args:
            vector_store: VectorStore instance for similarity search.
            embedder: Embedder for encoding queries.
            default_top_k: Default number of results.
            default_strategy: Default search strategy.
            hybrid_vector_weight: Weight for vector scores in hybrid mode.
            hybrid_keyword_weight: Weight for keyword scores in hybrid mode.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.default_top_k = default_top_k
        self.default_strategy = SearchStrategy(default_strategy)
        self.hybrid_vector_weight = hybrid_vector_weight
        self.hybrid_keyword_weight = hybrid_keyword_weight

        # Lazy-loaded BM25 index per collection
        self._bm25_indices: dict[str, Any] = {}

    async def search(
        self,
        query: str,
        collection_id: str,
        options: SearchOptions | None = None,
        multi_query: bool = False,
    ) -> RetrievalResult:
        """Execute a retrieval search.

        Args:
            query: The user's search query.
            collection_id: Vector collection to search.
            options: Optional search configuration.
            multi_query: If True, expand the query into multiple variants
                using an LLM, search each, and merge/deduplicate results.

        Returns:
            RetrievalResult with scored chunks.

        Raises:
            RetrievalError: On search failure.
        """
        opts = options or SearchOptions(
            strategy=self.default_strategy,
            top_k=self.default_top_k,
            vector_weight=self.hybrid_vector_weight,
            keyword_weight=self.hybrid_keyword_weight,
        )

        try:
            if multi_query:
                return await self._multi_query_search(query, collection_id, opts)

            return await self._single_search(query, collection_id, opts)

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Search failed: {exc}") from exc

    async def _single_search(
        self, query: str, collection_id: str, opts: SearchOptions
    ) -> RetrievalResult:
        """Execute a single-query retrieval search."""
        strategy = opts.strategy

        if strategy == SearchStrategy.VECTOR:
            chunks = await self._vector_search(query, collection_id, opts)
        elif strategy == SearchStrategy.KEYWORD:
            chunks = await self._keyword_search(query, collection_id, opts)
        elif strategy == SearchStrategy.HYBRID:
            chunks = await self._hybrid_search(query, collection_id, opts)
        else:
            raise RetrievalError(f"Unknown search strategy: {strategy}")

        # Apply score threshold
        if opts.score_threshold > 0:
            chunks = [c for c in chunks if c.score >= opts.score_threshold]

        return RetrievalResult(
            chunks=chunks,
            strategy=strategy.value,
            total_candidates=len(chunks),
            query=query,
        )

    async def _multi_query_search(
        self, query: str, collection_id: str, opts: SearchOptions
    ) -> RetrievalResult:
        """Expand query into variants, search each, and merge results."""
        from core.retrieval.multi_query import MultiQueryExpander

        expander = MultiQueryExpander()
        queries = await expander.expand(query)

        # Search with each query variant
        all_chunks: dict[str, ScoredChunk] = {}

        for q in queries:
            result = await self._single_search(q, collection_id, opts)
            for chunk in result.chunks:
                key = chunk.chunk_id or chunk.content[:120]
                if key in all_chunks:
                    # Keep the highest score
                    if chunk.score > all_chunks[key].score:
                        all_chunks[key] = chunk
                else:
                    all_chunks[key] = chunk

        # Sort by score and limit to top_k
        merged = sorted(all_chunks.values(), key=lambda c: c.score, reverse=True)
        merged = merged[: opts.top_k]

        logger.info(
            "Multi-query search: %d queries -> %d unique results (top %d)",
            len(queries), len(all_chunks), len(merged),
        )

        return RetrievalResult(
            chunks=merged,
            strategy=f"multi_query_{opts.strategy.value}",
            total_candidates=len(all_chunks),
            query=query,
        )

    # ── Vector search ──────────────────────────────────────────────────────

    async def _vector_search(
        self, query: str, collection_id: str, opts: SearchOptions
    ) -> list[ScoredChunk]:
        """Perform semantic similarity search via embeddings."""
        query_vector = await self.embedder.embed_query(query)
        results = await self.vector_store.search(
            collection_name=collection_id,
            query_vector=query_vector,
            limit=opts.top_k,
            filters=opts.filters,
        )

        return [
            ScoredChunk(
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                metadata={k: v for k, v in r.items() if k not in ("content", "score", "id")},
                chunk_id=r.get("id", ""),
            )
            for r in results
        ]

    # ── Keyword search ─────────────────────────────────────────────────────

    async def _keyword_search(
        self, query: str, collection_id: str, opts: SearchOptions
    ) -> list[ScoredChunk]:
        """Perform BM25 keyword search over stored documents.

        Retrieves all documents from the collection, builds a BM25 index,
        and returns the top-k matches.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise RetrievalError("rank-bm25 is required for keyword search: pip install rank-bm25")

        # Retrieve corpus from vector store (scroll all payloads)
        all_docs = await self.vector_store.scroll(
            collection_name=collection_id, limit=10000
        )

        if not all_docs:
            return []

        # Build or reuse BM25 index
        corpus_tokens = [doc.get("content", "").lower().split() for doc in all_docs]
        bm25 = BM25Okapi(corpus_tokens)

        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Pair scores with documents and sort
        scored = sorted(zip(scores, all_docs), key=lambda x: x[0], reverse=True)

        results: list[ScoredChunk] = []
        for score, doc in scored[: opts.top_k]:
            if score <= 0:
                break
            results.append(
                ScoredChunk(
                    content=doc.get("content", ""),
                    score=float(score),
                    metadata={k: v for k, v in doc.items() if k not in ("content", "id")},
                    chunk_id=doc.get("id", ""),
                )
            )

        return results

    # ── Hybrid search ──────────────────────────────────────────────────────

    async def _hybrid_search(
        self, query: str, collection_id: str, opts: SearchOptions
    ) -> list[ScoredChunk]:
        """Combine vector and keyword search with weighted scoring."""
        vector_results = await self._vector_search(query, collection_id, opts)
        keyword_results = await self._keyword_search(query, collection_id, opts)

        # Normalise scores to [0, 1]
        vector_results = self._normalize_scores(vector_results)
        keyword_results = self._normalize_scores(keyword_results)

        # Merge by chunk_id / content
        combined: dict[str, ScoredChunk] = {}

        for chunk in vector_results:
            key = chunk.chunk_id or chunk.content[:100]
            combined[key] = ScoredChunk(
                content=chunk.content,
                score=chunk.score * opts.vector_weight,
                metadata=chunk.metadata,
                chunk_id=chunk.chunk_id,
            )

        for chunk in keyword_results:
            key = chunk.chunk_id or chunk.content[:100]
            if key in combined:
                combined[key].score += chunk.score * opts.keyword_weight
            else:
                combined[key] = ScoredChunk(
                    content=chunk.content,
                    score=chunk.score * opts.keyword_weight,
                    metadata=chunk.metadata,
                    chunk_id=chunk.chunk_id,
                )

        ranked = sorted(combined.values(), key=lambda c: c.score, reverse=True)
        return ranked[: opts.top_k]

    @staticmethod
    def _normalize_scores(chunks: list[ScoredChunk]) -> list[ScoredChunk]:
        """Min-max normalise scores to [0, 1]."""
        if not chunks:
            return chunks
        max_score = max(c.score for c in chunks)
        min_score = min(c.score for c in chunks)
        spread = max_score - min_score
        if spread == 0:
            for c in chunks:
                c.score = 1.0
        else:
            for c in chunks:
                c.score = (c.score - min_score) / spread
        return chunks
