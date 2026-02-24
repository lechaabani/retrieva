"""Pydantic schemas for the first-time setup flow."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SetupStatusResponse(BaseModel):
    needs_setup: bool


class SetupInitRequest(BaseModel):
    platform_name: str = Field(default="Retrieva", min_length=1, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=128)
    embedding_provider: str = Field(
        default="openai", description="openai | ollama | cohere | google"
    )
    embedding_api_key: Optional[str] = Field(
        default=None, description="API key for embedding provider"
    )
    generation_provider: str = Field(
        default="openai", description="openai | anthropic | google | ollama"
    )
    generation_model: Optional[str] = Field(
        default=None, description="LLM model name (e.g. gpt-4o-mini, claude-sonnet-4-20250514)"
    )
    generation_api_key: Optional[str] = Field(
        default=None, description="API key for generation provider"
    )
    collection_name: Optional[str] = Field(default=None, max_length=255)


class SetupInitResponse(BaseModel):
    tenant_id: str
    user_id: str
    api_key: str
    collection_id: Optional[str] = None
    message: str = "Setup complete"


class ConnectionTestRequest(BaseModel):
    service: str = Field(
        ..., description="Service to test: embedding, generation, qdrant, redis, database"
    )
    provider: Optional[str] = Field(
        default=None, description="Provider: openai, ollama, cohere, google, anthropic"
    )
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")


class ConnectionTestResponse(BaseModel):
    service: str
    status: str = Field(..., description="ok or error")
    latency_ms: float
    message: str
    details: Optional[dict] = None
