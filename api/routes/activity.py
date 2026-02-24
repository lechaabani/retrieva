"""Activity feed endpoint -- aggregates recent platform events into a timeline."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, text, union_all, literal_column, literal
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.api_key import ApiKey
from api.models.collection import Collection
from api.models.document import Document
from api.models.query_log import QueryLog
from api.models.tenant import Tenant
from api.schemas.activity import ActivityEvent, ActivityFeedResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Activity"])


@router.get(
    "/activity/recent",
    response_model=ActivityFeedResponse,
    status_code=status.HTTP_200_OK,
    summary="Recent Activity Feed",
    description="Returns recent platform events across documents, queries, collections, and API keys.",
)
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ActivityFeedResponse:
    """Build a unified activity timeline from multiple database tables."""

    events: list[ActivityEvent] = []
    tenant_id = tenant.id

    # ---- Documents (ingested) ------------------------------------------------
    try:
        stmt = (
            select(Document)
            .join(Collection, Document.collection_id == Collection.id)
            .where(Collection.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        documents = result.scalars().all()

        for doc in documents:
            event_type = "error" if doc.status.value == "error" else "document_ingested"
            title = (
                f"Document ingested: {doc.title}"
                if event_type == "document_ingested"
                else f"Ingestion error: {doc.title}"
            )
            events.append(
                ActivityEvent(
                    id=f"doc-{doc.id}",
                    type=event_type,
                    title=title,
                    description=f"{doc.chunks_count} chunks — via {doc.source_connector}",
                    timestamp=doc.created_at,
                    metadata={
                        "document_id": str(doc.id),
                        "collection_id": str(doc.collection_id),
                        "status": doc.status.value,
                        "chunks_count": doc.chunks_count,
                        "source_connector": doc.source_connector,
                    },
                )
            )
    except Exception as exc:
        logger.warning("Failed to fetch document events: %s", exc)

    # ---- Queries -------------------------------------------------------------
    try:
        stmt = (
            select(QueryLog)
            .where(QueryLog.tenant_id == tenant_id)
            .order_by(QueryLog.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()

        for log in logs:
            question_preview = (
                log.question[:80] + "..." if len(log.question) > 80 else log.question
            )
            conf_str = (
                f" — confidence {log.confidence:.0%}" if log.confidence is not None else ""
            )
            events.append(
                ActivityEvent(
                    id=f"query-{log.id}",
                    type="query_made",
                    title=f"Query: {question_preview}",
                    description=f"{log.latency_ms or 0}ms{conf_str}",
                    timestamp=log.created_at,
                    metadata={
                        "query_log_id": str(log.id),
                        "collection_id": str(log.collection_id) if log.collection_id else None,
                        "confidence": log.confidence,
                        "latency_ms": log.latency_ms,
                        "tokens_used": log.tokens_used,
                    },
                )
            )
    except Exception as exc:
        logger.warning("Failed to fetch query events: %s", exc)

    # ---- Collections ---------------------------------------------------------
    try:
        stmt = (
            select(Collection)
            .where(Collection.tenant_id == tenant_id)
            .order_by(Collection.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        collections = result.scalars().all()

        for coll in collections:
            events.append(
                ActivityEvent(
                    id=f"coll-{coll.id}",
                    type="collection_created",
                    title=f"Collection created: {coll.name}",
                    description=coll.description or "",
                    timestamp=coll.created_at,
                    metadata={
                        "collection_id": str(coll.id),
                        "name": coll.name,
                    },
                )
            )
    except Exception as exc:
        logger.warning("Failed to fetch collection events: %s", exc)

    # ---- API Keys ------------------------------------------------------------
    try:
        stmt = (
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        keys = result.scalars().all()

        for key in keys:
            events.append(
                ActivityEvent(
                    id=f"key-{key.id}",
                    type="api_key_created",
                    title=f"API key created: {key.name}",
                    description=f"Type: {key.key_type}",
                    timestamp=key.created_at,
                    metadata={
                        "api_key_id": str(key.id),
                        "key_type": key.key_type,
                        "name": key.name,
                    },
                )
            )
    except Exception as exc:
        logger.warning("Failed to fetch API key events: %s", exc)

    # ---- Analytics events (optional table, graceful fallback) ----------------
    try:
        check = await db.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables"
                "  WHERE table_name = 'analytics_events'"
                ")"
            )
        )
        table_exists = check.scalar()

        if table_exists:
            rows = await db.execute(
                text(
                    "SELECT id, event_type, title, description, created_at, metadata "
                    "FROM analytics_events "
                    "WHERE tenant_id = :tid "
                    "ORDER BY created_at DESC LIMIT :lim"
                ),
                {"tid": str(tenant_id), "lim": limit},
            )
            for row in rows:
                events.append(
                    ActivityEvent(
                        id=f"evt-{row.id}",
                        type=row.event_type or "info",
                        title=row.title or "Event",
                        description=row.description or "",
                        timestamp=row.created_at,
                        metadata=row.metadata if isinstance(row.metadata, dict) else {},
                    )
                )
    except Exception as exc:
        logger.debug("analytics_events table not available (non-fatal): %s", exc)

    # ---- Sort everything by timestamp desc and trim to limit -----------------
    events.sort(key=lambda e: e.timestamp, reverse=True)
    events = events[:limit]

    return ActivityFeedResponse(events=events, total_count=len(events))
