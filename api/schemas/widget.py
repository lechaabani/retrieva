"""Pydantic schemas for widget configuration endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WidgetConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    widget_type: str = Field(..., pattern=r"^(chatbot|search)$")
    collection_id: Optional[UUID] = None
    config: dict = Field(default_factory=dict)
    is_active: bool = True


class WidgetConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    collection_id: Optional[UUID] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class WidgetConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    widget_type: str
    collection_id: Optional[UUID] = None
    config: dict
    public_api_key_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    raw_public_key: Optional[str] = None  # Only set on creation

    model_config = {"from_attributes": True}


class WidgetEmbedResponse(BaseModel):
    widget_id: UUID
    embed_code: str
    public_key_prefix: Optional[str] = None


class WidgetQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    widget_id: UUID


class WidgetSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    widget_id: UUID
    top_k: int = Field(default=5, ge=1, le=20)
