"""Collection comparison endpoints."""

import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.chunk import Chunk
from api.models.collection import Collection
from api.models.document import Document
from api.models.tenant import Tenant
from api.schemas.compare import (
    CollectionStats,
    CompareRequest,
    CompareResponse,
    QueryResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compare"])


async def _gather_stats(
    collection_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> CollectionStats:
    """Gather aggregated statistics for a single collection."""
    # Fetch collection
    stmt = select(Collection).where(
        Collection.id == collection_id,
        Collection.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    col = result.scalar_one_or_none()

    if col is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found.",
        )

    # Document count
    doc_count = (
        await db.execute(
            select(func.count(Document.id)).where(
                Document.collection_id == collection_id
            )
        )
    ).scalar() or 0

    # Chunk count
    chunk_count = (
        await db.execute(
            select(func.count(Chunk.id)).where(
                Chunk.collection_id == collection_id
            )
        )
    ).scalar() or 0

    # Total content length (characters) and average chunk size
    length_result = await db.execute(
        select(
            func.sum(func.length(Chunk.content)),
            func.avg(func.length(Chunk.content)),
        ).where(Chunk.collection_id == collection_id)
    )
    row = length_result.one()
    total_chars = row[0] or 0
    avg_chars = row[1] or 0.0

    total_words = int(total_chars / 5)  # approximate words
    avg_chunk_size = round(float(avg_chars) / 5, 1)

    # Last updated: most recent document timestamp
    last_updated_result = await db.execute(
        select(func.max(Document.created_at)).where(
            Document.collection_id == collection_id
        )
    )
    last_updated = last_updated_result.scalar()

    return CollectionStats(
        id=col.id,
        name=col.name,
        doc_count=doc_count,
        chunk_count=chunk_count,
        total_words=total_words,
        avg_chunk_size=avg_chunk_size,
        last_updated=last_updated,
    )


async def _run_query(
    question: str,
    collection_name: str,
    tenant: Tenant,
    db: AsyncSession,
    request: Request,
) -> QueryResult:
    """Run a RAG query against a collection and return timing + results."""
    from api.routes.query import (
        _build_generation_engine,
        _build_reranker,
        _build_retrieval_engine,
        _resolve_collection,
    )
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    cfg = get_config()
    start = time.perf_counter()

    collection = await _resolve_collection(collection_name, tenant, db)

    retrieval_engine = _build_retrieval_engine()
    generation_engine = _build_generation_engine()
    reranker = _build_reranker()

    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=cfg.retrieval.default_top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )

    retrieval_result = await retrieval_engine.search(
        query=question,
        collection_id=str(collection.id),
        options=search_options,
    )

    chunks = retrieval_result.chunks

    if reranker and chunks:
        try:
            chunks = await reranker.rerank(
                query=question,
                chunks=chunks,
                top_k=cfg.retrieval.rerank_top_k,
            )
        except Exception as exc:
            logger.warning("Reranking failed during compare: %s", exc)

    generation_result = await generation_engine.generate(
        query=question,
        chunks=chunks,
        language="fr",
    )

    latency_ms = int((time.perf_counter() - start) * 1000)

    return QueryResult(
        answer=generation_result.answer,
        latency_ms=latency_ms,
        sources_count=len(chunks),
        confidence=generation_result.confidence,
    )


@router.post(
    "/collections/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Collections",
    description="Compare two collections side by side with optional query testing.",
)
async def compare_collections(
    request: Request,
    body: CompareRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    """Compare two collections by gathering stats and optionally querying both."""
    if body.collection_a_id == body.collection_b_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a collection with itself.",
        )

    stats_a = await _gather_stats(body.collection_a_id, tenant.id, db)
    stats_b = await _gather_stats(body.collection_b_id, tenant.id, db)

    query_a = None
    query_b = None

    if body.question:
        try:
            query_a = await _run_query(
                body.question, stats_a.name, tenant, db, request
            )
        except Exception as exc:
            logger.warning("Query against collection A failed: %s", exc)
            query_a = QueryResult(
                answer=f"Erreur: {exc}",
                latency_ms=0,
                sources_count=0,
                confidence=0.0,
            )

        try:
            query_b = await _run_query(
                body.question, stats_b.name, tenant, db, request
            )
        except Exception as exc:
            logger.warning("Query against collection B failed: %s", exc)
            query_b = QueryResult(
                answer=f"Erreur: {exc}",
                latency_ms=0,
                sources_count=0,
                confidence=0.0,
            )

    return CompareResponse(
        collection_a=stats_a,
        collection_b=stats_b,
        query_a=query_a,
        query_b=query_b,
    )
