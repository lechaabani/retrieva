"""RAG query and semantic search endpoints."""

import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.auth.permissions import check_collection_access
from api.database import get_db
from api.middleware.rate_limit import limiter, DEFAULT_QUERY_LIMIT, DEFAULT_SEARCH_LIMIT
from api.models.collection import Collection
from api.models.query_log import QueryLog
from api.models.tenant import Tenant
from api.schemas.query import (
    DebugChunk,
    DebugQueryResponse,
    DebugStep,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Source,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Query"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_collection(
    name: str, tenant: Tenant, db: AsyncSession
) -> Collection:
    """Look up a collection by name within the tenant scope."""
    stmt = select(Collection).where(
        Collection.tenant_id == tenant.id,
        Collection.name == name,
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' not found.",
        )
    return collection


async def _check_permission(
    request: Request, collection: Collection, db: AsyncSession
) -> None:
    """Check if the current user (if JWT-authenticated) has access to the collection.

    API-key-only requests skip permission checks (they are scoped to tenant).
    JWT-authenticated users are checked against CollectionPermission records.
    """
    from api.auth.jwt import get_current_user
    from api.models.user import User

    try:
        # Try to extract user from JWT (optional — API key auth doesn't provide a user)
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        _bearer = HTTPBearer(auto_error=False)
        # Check if there's a Bearer token in the request
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from api.auth.jwt import verify_token
            token = auth_header[7:]
            payload = verify_token(token)
            user_id = payload.get("sub")
            if user_id:
                from sqlalchemy import select as sa_select
                stmt = sa_select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    has_access = await check_collection_access(user, collection, db)
                    if not has_access:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Role '{user.role}' does not have access to collection '{collection.name}'.",
                        )
    except HTTPException:
        raise
    except Exception:
        # If JWT parsing fails, user is likely using API key auth — skip permission check
        pass


def _build_retrieval_engine():
    """Build a properly configured RetrievalEngine from platform config."""
    from core.config import get_config
    from core.ingestion.embedders import get_embedder
    from core.retrieval.engine import RetrievalEngine
    from core.vector_store import VectorStore

    cfg = get_config()

    embedder = get_embedder(
        provider=cfg.ingestion.embedding_provider,
        model=cfg.ingestion.default_embedding_model,
    )

    vector_store = VectorStore(
        host=cfg.vector_db.host,
        port=cfg.vector_db.port,
        grpc_port=cfg.vector_db.grpc_port,
        api_key=cfg.vector_db.api_key,
        prefer_grpc=cfg.vector_db.prefer_grpc,
        collection_prefix=cfg.vector_db.collection_prefix,
    )

    return RetrievalEngine(
        vector_store=vector_store,
        embedder=embedder,
        default_top_k=cfg.retrieval.default_top_k,
        default_strategy=cfg.retrieval.default_strategy,
        hybrid_vector_weight=cfg.retrieval.hybrid_vector_weight,
        hybrid_keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )


def _build_generation_engine():
    """Build a properly configured GenerationEngine from platform config."""
    from core.config import get_config
    from core.generation.engine import GenerationEngine

    cfg = get_config()

    return GenerationEngine(
        provider=cfg.generation.default_provider,
        model=cfg.generation.default_model,
        temperature=cfg.generation.temperature,
        max_tokens=cfg.generation.max_tokens,
        max_context_chunks=cfg.generation.max_context_chunks,
        persona=cfg.generation.default_persona,
        enable_guardrails=cfg.generation.enable_guardrails,
        hallucination_threshold=cfg.generation.hallucination_threshold,
    )


def _build_reranker():
    """Build a Reranker if reranking is enabled, else return None."""
    from core.config import get_config
    from core.retrieval.reranker import Reranker

    cfg = get_config()
    if not cfg.retrieval.rerank_enabled:
        return None

    return Reranker(model_name=cfg.retrieval.rerank_model)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG Query",
    description="Run a full RAG pipeline: retrieve relevant chunks and generate an answer.",
)
@limiter.limit(DEFAULT_QUERY_LIMIT)
async def rag_query(
    request: Request,
    body: QueryRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Execute retrieval-augmented generation for the given question."""
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    start = time.perf_counter()

    collection = await _resolve_collection(body.collection, tenant, db)
    await _check_permission(request, collection, db)
    cfg = get_config()

    # Parse options with proper defaults from the Pydantic model
    opts = body.options
    top_k = opts.top_k if opts else cfg.retrieval.default_top_k
    include_sources = opts.include_sources if opts else True
    max_tokens = opts.max_tokens if opts else cfg.generation.max_tokens
    language = opts.language if opts else "en"

    # Build engines
    retrieval_engine = _build_retrieval_engine()
    generation_engine = _build_generation_engine()
    reranker = _build_reranker()

    # Retrieval phase
    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )

    retrieval_result = await retrieval_engine.search(
        query=body.question,
        collection_id=str(collection.id),
        options=search_options,
    )

    chunks = retrieval_result.chunks

    # Reranking phase
    if reranker and chunks:
        rerank_top_k = cfg.retrieval.rerank_top_k
        try:
            chunks = await reranker.rerank(
                query=body.question,
                chunks=chunks,
                top_k=rerank_top_k,
            )
            logger.info("Reranked %d chunks -> top %d", len(retrieval_result.chunks), rerank_top_k)
        except Exception as exc:
            logger.warning("Reranking failed, using original ranking: %s", exc)

    # Generation phase
    generation_result = await generation_engine.generate(
        query=body.question,
        chunks=chunks,
        language=language,
    )

    # Build source references
    sources = []
    if include_sources:
        for chunk in chunks:
            sources.append(
                Source(
                    document_id=chunk.metadata.get("document_id", chunk.chunk_id),
                    chunk_id=chunk.chunk_id or chunk.metadata.get("id", ""),
                    title=chunk.metadata.get("title", ""),
                    content=chunk.content[:500],
                    score=chunk.score,
                    metadata={
                        k: v for k, v in chunk.metadata.items()
                        if k not in ("document_id", "title", "content", "id")
                    },
                )
            )

    latency_ms = int((time.perf_counter() - start) * 1000)

    # Log the query
    log_entry = QueryLog(
        tenant_id=tenant.id,
        collection_id=collection.id,
        question=body.question,
        answer=generation_result.answer,
        sources=[s.model_dump(mode="json") for s in sources],
        confidence=generation_result.confidence,
        tokens_used=generation_result.tokens_used,
        latency_ms=latency_ms,
    )
    db.add(log_entry)
    await db.flush()

    # Dispatch webhook notification (fire-and-forget)
    try:
        from core.webhooks import WebhookDispatcher

        dispatcher = WebhookDispatcher(tenant_id=str(tenant.id))
        await dispatcher.dispatch(
            event="query_completed",
            data={
                "question": body.question,
                "collection": body.collection,
                "confidence": generation_result.confidence,
                "tokens_used": generation_result.tokens_used,
                "latency_ms": latency_ms,
                "sources_count": len(sources),
            },
        )
    except Exception as wh_exc:
        logger.warning("Webhook dispatch failed (non-fatal): %s", wh_exc)

    return QueryResponse(
        answer=generation_result.answer,
        sources=sources,
        confidence=generation_result.confidence,
        tokens_used=generation_result.tokens_used,
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search",
    description="Retrieve relevant document chunks without generating an answer.",
)
@limiter.limit(DEFAULT_SEARCH_LIMIT)
async def semantic_search(
    request: Request,
    body: SearchRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Run semantic search against a collection and return ranked chunks."""
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    collection = await _resolve_collection(body.collection, tenant, db)
    await _check_permission(request, collection, db)
    cfg = get_config()

    retrieval_engine = _build_retrieval_engine()
    reranker = _build_reranker()

    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=body.top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
        filters=body.filters,
    )

    retrieval_result = await retrieval_engine.search(
        query=body.query,
        collection_id=str(collection.id),
        options=search_options,
    )

    chunks = retrieval_result.chunks

    # Reranking phase
    if reranker and chunks:
        try:
            chunks = await reranker.rerank(
                query=body.query,
                chunks=chunks,
                top_k=body.top_k,
            )
        except Exception as exc:
            logger.warning("Reranking failed, using original ranking: %s", exc)

    results = [
        SearchResult(
            chunk_id=chunk.chunk_id or chunk.metadata.get("id", ""),
            document_id=chunk.metadata.get("document_id", chunk.chunk_id),
            title=chunk.metadata.get("title", ""),
            content=chunk.content[:500],
            score=chunk.score,
            metadata={
                k: v for k, v in chunk.metadata.items()
                if k not in ("document_id", "title", "content", "id")
            },
        )
        for chunk in chunks
    ]

    return SearchResponse(results=results, total=len(results))


@router.post(
    "/query/debug",
    response_model=DebugQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG Query Debug",
    description="Run the full RAG pipeline with per-step timing and intermediate results.",
)
@limiter.limit(DEFAULT_QUERY_LIMIT)
async def rag_query_debug(
    request: Request,
    body: QueryRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> DebugQueryResponse:
    """Execute retrieval-augmented generation and return detailed debug data for each step."""
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    pipeline_start = time.perf_counter()

    collection = await _resolve_collection(body.collection, tenant, db)
    await _check_permission(request, collection, db)
    cfg = get_config()

    # Parse options with proper defaults from the Pydantic model
    opts = body.options
    top_k = opts.top_k if opts else cfg.retrieval.default_top_k
    include_sources = opts.include_sources if opts else True
    language = opts.language if opts else "en"

    steps: list[DebugStep] = []

    # Build engines
    retrieval_engine = _build_retrieval_engine()
    generation_engine = _build_generation_engine()
    reranker = _build_reranker()

    # ------------------------------------------------------------------
    # Step 1: Embedding
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    query_vector = await retrieval_engine.embedder.embed(body.question)
    t1 = time.perf_counter()

    steps.append(
        DebugStep(
            name="embedding",
            label="Query Embedding",
            duration_ms=int((t1 - t0) * 1000),
            details={
                "provider": cfg.ingestion.embedding_provider,
                "model": cfg.ingestion.default_embedding_model,
                "dimensions": len(query_vector) if isinstance(query_vector, (list, tuple)) else 0,
            },
        )
    )

    # ------------------------------------------------------------------
    # Step 2: Retrieval (vector search)
    # ------------------------------------------------------------------
    t0 = time.perf_counter()

    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )

    retrieval_result = await retrieval_engine.search(
        query=body.question,
        collection_id=str(collection.id),
        options=search_options,
    )

    chunks = retrieval_result.chunks
    t1 = time.perf_counter()

    steps.append(
        DebugStep(
            name="retrieval",
            label="Vector Search",
            duration_ms=int((t1 - t0) * 1000),
            details={
                "strategy": cfg.retrieval.default_strategy,
                "top_k": top_k,
                "results_found": len(chunks),
            },
            chunks=[
                DebugChunk(
                    content=c.content[:200],
                    score=c.score,
                    doc_id=c.metadata.get("document_id", c.chunk_id or ""),
                )
                for c in chunks
            ],
        )
    )

    # ------------------------------------------------------------------
    # Step 3: Reranking (optional)
    # ------------------------------------------------------------------
    if reranker and chunks:
        t0 = time.perf_counter()
        rerank_top_k = cfg.retrieval.rerank_top_k
        original_count = len(chunks)
        try:
            chunks = await reranker.rerank(
                query=body.question,
                chunks=chunks,
                top_k=rerank_top_k,
            )
            rerank_error = None
        except Exception as exc:
            logger.warning("Reranking failed, using original ranking: %s", exc)
            rerank_error = str(exc)
        t1 = time.perf_counter()

        step_details: dict = {
            "model": cfg.retrieval.rerank_model,
            "input_chunks": original_count,
            "output_chunks": len(chunks),
        }
        if rerank_error:
            step_details["error"] = rerank_error

        steps.append(
            DebugStep(
                name="reranking",
                label="Reranking",
                duration_ms=int((t1 - t0) * 1000),
                details=step_details,
                chunks=[
                    DebugChunk(
                        content=c.content[:200],
                        score=c.score,
                        doc_id=c.metadata.get("document_id", c.chunk_id or ""),
                    )
                    for c in chunks
                ],
            )
        )

    # ------------------------------------------------------------------
    # Step 4: Generation
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    generation_result = await generation_engine.generate(
        query=body.question,
        chunks=chunks,
        language=language,
    )
    t1 = time.perf_counter()

    steps.append(
        DebugStep(
            name="generation",
            label="Answer Generation",
            duration_ms=int((t1 - t0) * 1000),
            details={
                "provider": cfg.generation.default_provider,
                "model": cfg.generation.default_model,
                "tokens_used": generation_result.tokens_used,
                "confidence": generation_result.confidence,
            },
        )
    )

    # ------------------------------------------------------------------
    # Build source references
    # ------------------------------------------------------------------
    sources: list[Source] = []
    if include_sources:
        for chunk in chunks:
            sources.append(
                Source(
                    document_id=chunk.metadata.get("document_id", chunk.chunk_id),
                    chunk_id=chunk.chunk_id or chunk.metadata.get("id", ""),
                    title=chunk.metadata.get("title", ""),
                    content=chunk.content[:500],
                    score=chunk.score,
                    metadata={
                        k: v for k, v in chunk.metadata.items()
                        if k not in ("document_id", "title", "content", "id")
                    },
                )
            )

    total_latency_ms = int((time.perf_counter() - pipeline_start) * 1000)

    return DebugQueryResponse(
        answer=generation_result.answer,
        confidence=generation_result.confidence,
        total_latency_ms=total_latency_ms,
        steps=steps,
        sources=sources,
    )
