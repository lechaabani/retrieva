"""Public widget serving endpoints (JS, CSS, config, query, search)."""

import logging
import os
import time
from pathlib import Path
from typing import Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_public_tenant
from api.database import get_db
from api.middleware.rate_limit import limiter
from api.models.api_key import ApiKey
from api.models.tenant import Tenant
from api.models.widget_config import WidgetConfig
from api.schemas.widget import WidgetQueryRequest, WidgetSearchRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/widget", tags=["Widget"])

# Path to template plugin assets
_ASSETS_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "templates"

_WIDGET_ASSET_MAP = {
    "chatbot": {"js": "chatbot-widget/assets/widget.js", "css": "chatbot-widget/assets/widget.css"},
    "search": {"js": "search-bar/assets/search.js", "css": "search-bar/assets/search.css"},
}

DEFAULT_WIDGET_QUERY_LIMIT = "30/minute"
DEFAULT_WIDGET_SEARCH_LIMIT = "60/minute"


# ---------------------------------------------------------------------------
# Static asset serving
# ---------------------------------------------------------------------------

@router.get("/{widget_type}.js", summary="Serve Widget JavaScript")
async def serve_widget_js(widget_type: str) -> Response:
    """Serve the widget JavaScript file with CORS headers."""
    if widget_type not in _WIDGET_ASSET_MAP:
        raise HTTPException(status_code=404, detail="Unknown widget type.")
    asset_path = _ASSETS_ROOT / _WIDGET_ASSET_MAP[widget_type]["js"]
    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Widget asset not found.")
    content = asset_path.read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/{widget_type}.css", summary="Serve Widget CSS")
async def serve_widget_css(widget_type: str) -> Response:
    """Serve the widget CSS file with CORS headers."""
    if widget_type not in _WIDGET_ASSET_MAP:
        raise HTTPException(status_code=404, detail="Unknown widget type.")
    asset_path = _ASSETS_ROOT / _WIDGET_ASSET_MAP[widget_type]["css"]
    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Widget asset not found.")
    content = asset_path.read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ---------------------------------------------------------------------------
# Widget config (public, no auth — UUID is capability token)
# ---------------------------------------------------------------------------

@router.get("/config/{widget_id}", summary="Get Widget Config")
async def get_widget_config(
    widget_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the visual configuration for a widget (no auth required)."""
    stmt = select(WidgetConfig).where(
        WidgetConfig.id == widget_id,
        WidgetConfig.is_active.is_(True),
    )
    result = await db.execute(stmt)
    widget = result.scalar_one_or_none()
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found or inactive.")

    # Only expose visual config, never keys or tenant data
    cfg = widget.config or {}
    return {
        "widget_id": str(widget.id),
        "widget_type": widget.widget_type,
        "title": cfg.get("title", "Chat with us"),
        "welcome_message": cfg.get("welcome_message", ""),
        "position": cfg.get("position", "bottom-right"),
        "primary_color": cfg.get("primary_color", "#4F46E5"),
        "text_color": cfg.get("text_color", "#FFFFFF"),
        "placeholder": cfg.get("placeholder", "Type a message..."),
        "show_sources": cfg.get("show_sources", False),
    }


# ---------------------------------------------------------------------------
# Public query/search (requires public API key)
# ---------------------------------------------------------------------------

@router.post("/query", summary="Widget RAG Query")
@limiter.limit(DEFAULT_WIDGET_QUERY_LIMIT)
async def widget_query(
    request: Request,
    body: WidgetQueryRequest,
    auth: Tuple[Tenant, ApiKey] = Depends(get_public_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public RAG query endpoint for embedded widgets."""
    tenant, api_key = auth

    # Look up widget config
    stmt = select(WidgetConfig).where(
        WidgetConfig.id == body.widget_id,
        WidgetConfig.tenant_id == tenant.id,
        WidgetConfig.is_active.is_(True),
    )
    result = await db.execute(stmt)
    widget = result.scalar_one_or_none()
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found or inactive.")

    if not widget.collection_id:
        raise HTTPException(status_code=400, detail="Widget has no collection configured.")

    start = time.perf_counter()

    # Reuse the retrieval + generation pipeline from query.py
    from api.routes.query import _build_retrieval_engine, _build_generation_engine, _build_reranker
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    cfg = get_config()
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
        query=body.question,
        collection_id=str(widget.collection_id),
        options=search_options,
    )

    chunks = retrieval_result.chunks

    if reranker and chunks:
        try:
            chunks = await reranker.rerank(
                query=body.question,
                chunks=chunks,
                top_k=cfg.retrieval.rerank_top_k,
            )
        except Exception as exc:
            logger.warning("Widget reranking failed: %s", exc)

    generation_result = await generation_engine.generate(
        query=body.question,
        chunks=chunks,
    )

    latency_ms = int((time.perf_counter() - start) * 1000)

    # Build sources
    widget_cfg = widget.config or {}
    sources = []
    if widget_cfg.get("show_sources", False):
        for chunk in chunks[:5]:
            sources.append({
                "title": chunk.metadata.get("title", ""),
                "content": chunk.content[:300],
                "score": chunk.score,
            })

    return {
        "answer": generation_result.answer,
        "sources": sources,
        "latency_ms": latency_ms,
    }


@router.post("/search", summary="Widget Semantic Search")
@limiter.limit(DEFAULT_WIDGET_SEARCH_LIMIT)
async def widget_search(
    request: Request,
    body: WidgetSearchRequest,
    auth: Tuple[Tenant, ApiKey] = Depends(get_public_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public search endpoint for embedded search widgets."""
    tenant, api_key = auth

    stmt = select(WidgetConfig).where(
        WidgetConfig.id == body.widget_id,
        WidgetConfig.tenant_id == tenant.id,
        WidgetConfig.is_active.is_(True),
    )
    result = await db.execute(stmt)
    widget = result.scalar_one_or_none()
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found or inactive.")

    if not widget.collection_id:
        raise HTTPException(status_code=400, detail="Widget has no collection configured.")

    from api.routes.query import _build_retrieval_engine, _build_reranker
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    cfg = get_config()
    retrieval_engine = _build_retrieval_engine()
    reranker = _build_reranker()

    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=body.top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )

    retrieval_result = await retrieval_engine.search(
        query=body.query,
        collection_id=str(widget.collection_id),
        options=search_options,
    )

    chunks = retrieval_result.chunks

    if reranker and chunks:
        try:
            chunks = await reranker.rerank(query=body.query, chunks=chunks, top_k=body.top_k)
        except Exception:
            pass

    results = [
        {
            "title": chunk.metadata.get("title", ""),
            "content": chunk.content[:300],
            "score": chunk.score,
        }
        for chunk in chunks
    ]

    return {"results": results, "total": len(results)}
