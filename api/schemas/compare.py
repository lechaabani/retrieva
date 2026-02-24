"""Schemas for collection comparison endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    """Payload for comparing two collections."""

    collection_a_id: UUID = Field(..., description="First collection ID")
    collection_b_id: UUID = Field(..., description="Second collection ID")
    question: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional question to run against both collections",
    )


class CollectionStats(BaseModel):
    """Aggregated statistics for a single collection."""

    id: UUID
    name: str
    doc_count: int = 0
    chunk_count: int = 0
    total_words: int = 0
    avg_chunk_size: float = 0.0
    last_updated: Optional[datetime] = None


class QueryResult(BaseModel):
    """Result of running a question against a single collection."""

    answer: str
    latency_ms: int
    sources_count: int = 0
    confidence: float = 0.0


class CompareResponse(BaseModel):
    """Full comparison response for two collections."""

    collection_a: CollectionStats
    collection_b: CollectionStats
    query_a: Optional[QueryResult] = None
    query_b: Optional[QueryResult] = None
