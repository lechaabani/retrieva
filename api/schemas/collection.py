"""Schemas for collection management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    """Payload for creating a new collection."""

    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(default=None, max_length=2000, description="Human-readable description")
    config: dict = Field(default_factory=dict, description="Collection-level configuration overrides")


class CollectionUpdate(BaseModel):
    """Payload for updating an existing collection."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    config: Optional[dict] = None


class CollectionResponse(BaseModel):
    """Serialised collection returned by the API."""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    config: dict = Field(default_factory=dict)
    created_at: datetime
    documents_count: int = 0
    chunks_count: int = 0

    model_config = {"from_attributes": True}


class CollectionList(BaseModel):
    """Paginated list of collections."""

    collections: list[CollectionResponse] = Field(default_factory=list)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
