"""Schemas for authentication and authorization endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ApiKeyCreate(BaseModel):
    """Payload for generating a new API key."""

    name: str = Field(..., min_length=1, max_length=255, description="Human-readable key name")
    permissions: dict = Field(default_factory=dict, description="Permission map (e.g. {'query': true, 'ingest': true})")
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365, description="Days until expiry (null = never)")


class ApiKeyResponse(BaseModel):
    """API key metadata returned by the API. The raw key is only shown on creation."""

    id: UUID
    name: str
    key_prefix: str = Field(description="First 8 characters of the key for identification")
    permissions: dict = Field(default_factory=dict)
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only once when a key is first created. Contains the raw key."""

    raw_key: str = Field(description="The full API key. Store it securely; it cannot be retrieved again.")


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Extended response returned after successful login, including session API key and user info."""

    access_token: str
    token_type: str = "bearer"
    api_key: str
    user: dict  # {id, email, role}
    tenant_name: str


class UserCreate(BaseModel):
    """Payload for creating a new user account."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")


class UserLogin(BaseModel):
    """Payload for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Serialised user returned by the API. Never includes the password hash."""

    id: UUID
    tenant_id: UUID
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
