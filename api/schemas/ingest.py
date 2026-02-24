"""Schemas for document ingestion endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class IngestTextRequest(BaseModel):
    """Payload for ingesting raw text content."""

    content: str = Field(..., min_length=1, description="The text content to ingest")
    title: str = Field(..., min_length=1, max_length=512, description="Document title")
    collection: str = Field(..., min_length=1, max_length=255, description="Target collection name")
    metadata: dict = Field(default_factory=dict, description="Arbitrary metadata to attach to the document")


class IngestUrlRequest(BaseModel):
    """Payload for ingesting content from a URL."""

    url: HttpUrl = Field(..., description="URL to crawl and ingest")
    collection: str = Field(..., min_length=1, max_length=255, description="Target collection name")
    crawl_depth: int = Field(default=0, ge=0, le=3, description="How many link levels to follow")
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    """Response returned after submitting an ingestion job."""

    document_id: UUID
    status: str = Field(description="Current processing status (e.g. 'processing')")
    chunks_count: int = Field(default=0, description="Number of chunks created (0 while still processing)")
    message: str = Field(description="Human-readable status message")
