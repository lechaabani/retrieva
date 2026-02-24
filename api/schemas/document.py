"""Schemas for document management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Payload for creating a document record."""

    collection_id: UUID
    source_connector: str = Field(..., max_length=100)
    source_id: Optional[str] = Field(default=None, max_length=512)
    title: str = Field(..., min_length=1, max_length=512)
    metadata: dict = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    """Serialised document returned by the API."""

    id: UUID
    collection_id: UUID
    source_connector: str
    source_id: Optional[str] = None
    title: str
    content_hash: Optional[str] = None
    metadata: dict = Field(default_factory=dict, validation_alias="doc_metadata")
    status: str
    chunks_count: int
    indexed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse] = Field(default_factory=list)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
