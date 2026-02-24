"""Query Analytics Dashboard endpoint."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select, cast, Date, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.collection import Collection
from api.models.query_log import QueryLog
from api.models.tenant import Tenant
from api.schemas.analytics_dashboard import (
    AnalyticsDashboardResponse,
    CollectionUsage,
    ConfidenceBucket,
    LatencyTrendPoint,
    TopQuestion,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics Dashboard"])


@router.get(
    "/analytics/dashboard",
    response_model=AnalyticsDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Analytics Dashboard",
    description="Returns aggregated query analytics: latency trends, top questions, confidence distribution, and more.",
)
async def analytics_dashboard(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsDashboardResponse:
    """Build and return the full analytics dashboard for the current tenant."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    thirty_days_ago = today_start - timedelta(days=30)

    base = select(QueryLog).where(QueryLog.tenant_id == tenant.id)

    # ── Summary stats ────────────────────────────────────────────────
    summary_stmt = select(
        func.count(QueryLog.id).label("total"),
        func.coalesce(func.avg(QueryLog.latency_ms), 0).label("avg_latency"),
        func.coalesce(func.avg(QueryLog.confidence), 0).label("avg_confidence"),
        func.count(
            case(
                (QueryLog.created_at >= today_start, QueryLog.id),
                else_=None,
            )
        ).label("today"),
        func.count(
            case(
                (QueryLog.created_at >= week_start, QueryLog.id),
                else_=None,
            )
        ).label("this_week"),
        func.count(
            case(
                (QueryLog.answer.is_(None), QueryLog.id),
                else_=None,
            )
        ).label("error_count"),
    ).where(QueryLog.tenant_id == tenant.id)

    result = await db.execute(summary_stmt)
    row = result.one()

    total_queries: int = row.total or 0
    avg_latency_ms: float = float(row.avg_latency or 0)
    avg_confidence: float = float(row.avg_confidence or 0)
    queries_today: int = row.today or 0
    queries_this_week: int = row.this_week or 0
    error_count: int = row.error_count or 0
    error_rate: float = (error_count / total_queries * 100) if total_queries > 0 else 0.0

    # ── Latency trend (last 30 days) ─────────────────────────────────
    trend_stmt = (
        select(
            cast(QueryLog.created_at, Date).label("date"),
            func.avg(QueryLog.latency_ms).label("avg_latency"),
            func.count(QueryLog.id).label("count"),
        )
        .where(
            and_(
                QueryLog.tenant_id == tenant.id,
                QueryLog.created_at >= thirty_days_ago,
            )
        )
        .group_by(cast(QueryLog.created_at, Date))
        .order_by(cast(QueryLog.created_at, Date))
    )

    trend_result = await db.execute(trend_stmt)
    latency_trend = [
        LatencyTrendPoint(
            date=str(r.date),
            avg_latency=round(float(r.avg_latency or 0), 1),
            count=r.count,
        )
        for r in trend_result.all()
    ]

    # ── Top 10 questions ─────────────────────────────────────────────
    top_q_stmt = (
        select(
            QueryLog.question,
            func.count(QueryLog.id).label("cnt"),
            func.avg(QueryLog.confidence).label("avg_conf"),
        )
        .where(QueryLog.tenant_id == tenant.id)
        .group_by(QueryLog.question)
        .order_by(func.count(QueryLog.id).desc())
        .limit(10)
    )

    top_q_result = await db.execute(top_q_stmt)
    top_questions = [
        TopQuestion(
            question=r.question,
            count=r.cnt,
            avg_confidence=round(float(r.avg_conf or 0), 3),
        )
        for r in top_q_result.all()
    ]

    # ── Confidence distribution (5 buckets) ──────────────────────────
    buckets_def = [
        ("0-0.2", 0.0, 0.2),
        ("0.2-0.4", 0.2, 0.4),
        ("0.4-0.6", 0.4, 0.6),
        ("0.6-0.8", 0.6, 0.8),
        ("0.8-1.0", 0.8, 1.01),  # slightly above 1 to include 1.0
    ]

    confidence_distribution: list[ConfidenceBucket] = []
    for label, lo, hi in buckets_def:
        bucket_stmt = (
            select(func.count(QueryLog.id))
            .where(
                and_(
                    QueryLog.tenant_id == tenant.id,
                    QueryLog.confidence.isnot(None),
                    QueryLog.confidence >= lo,
                    QueryLog.confidence < hi,
                )
            )
        )
        bucket_result = await db.execute(bucket_stmt)
        count = bucket_result.scalar() or 0
        confidence_distribution.append(ConfidenceBucket(bucket=label, count=count))

    # ── Collection usage (top 5) ─────────────────────────────────────
    coll_stmt = (
        select(
            Collection.name.label("collection_name"),
            func.count(QueryLog.id).label("query_count"),
        )
        .join(Collection, Collection.id == QueryLog.collection_id, isouter=True)
        .where(QueryLog.tenant_id == tenant.id)
        .group_by(Collection.name)
        .order_by(func.count(QueryLog.id).desc())
        .limit(5)
    )

    coll_result = await db.execute(coll_stmt)
    collection_usage = [
        CollectionUsage(
            collection_name=r.collection_name or "Unknown",
            query_count=r.query_count,
        )
        for r in coll_result.all()
    ]

    return AnalyticsDashboardResponse(
        total_queries=total_queries,
        avg_latency_ms=round(avg_latency_ms, 1),
        avg_confidence=round(avg_confidence, 3),
        queries_today=queries_today,
        queries_this_week=queries_this_week,
        latency_trend=latency_trend,
        top_questions=top_questions,
        confidence_distribution=confidence_distribution,
        collection_usage=collection_usage,
        error_rate=round(error_rate, 2),
    )
