"""Schemas for admin and analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class AnalyticsBucket(BaseModel):
    """A single time-bucket in the analytics breakdown."""

    date: str = Field(description="ISO date string for the bucket (e.g. '2025-06-15')")
    query_count: int = 0
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0


class AnalyticsResponse(BaseModel):
    """Aggregated query analytics for a tenant."""

    total_queries: int = 0
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    total_tokens_used: int = 0
    period_start: datetime
    period_end: datetime
    buckets: list[AnalyticsBucket] = Field(default_factory=list)


class TenantConfig(BaseModel):
    """Editable configuration for a tenant."""

    default_language: str = Field(default="en", max_length=10)
    default_top_k: int = Field(default=10, ge=1, le=100)
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    allowed_file_types: list[str] = Field(
        default_factory=lambda: ["pdf", "docx", "xlsx", "txt", "md", "csv"]
    )
    embedding_model: str = Field(default="text-embedding-3-small", max_length=255)
    generation_model: str = Field(default="gpt-4o", max_length=255)


class WebhookConfig(BaseModel):
    """Configuration for a webhook subscription."""

    url: HttpUrl = Field(description="URL to POST events to")
    events: list[str] = Field(
        ...,
        min_length=1,
        description="Events to subscribe to (e.g. ['document.indexed', 'query.completed'])",
    )
    secret: Optional[str] = Field(default=None, max_length=255, description="Shared secret for HMAC verification")
    active: bool = Field(default=True)


class WebhookResponse(BaseModel):
    """Serialised webhook returned by the API."""

    id: UUID
    url: str
    events: list[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryLogResponse(BaseModel):
    """A single query log entry."""

    id: UUID
    tenant_id: UUID
    collection_id: Optional[UUID] = None
    question: str
    answer: Optional[str] = None
    sources: list = Field(default_factory=list)
    confidence: Optional[float] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryLogList(BaseModel):
    """Paginated list of query log entries."""

    logs: list[QueryLogResponse] = Field(default_factory=list)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
