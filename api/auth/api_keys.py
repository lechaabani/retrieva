"""API key generation, verification, and FastAPI dependency for tenant auth."""

import os
import secrets
from datetime import datetime, timezone
from typing import Tuple

import bcrypt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import get_db
from api.models.api_key import ApiKey
from api.models.tenant import Tenant

_KEY_PREFIX = "rtv_"
_PUBLIC_KEY_PREFIX = "rtv_pub_"
_KEY_LENGTH = 48

_bearer_scheme = HTTPBearer(auto_error=False)


def _hash_password(secret: str) -> str:
    """Hash a secret string using bcrypt."""
    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(secret: str, hashed: str) -> bool:
    """Verify a secret against a bcrypt hash."""
    return bcrypt.checkpw(secret.encode("utf-8"), hashed.encode("utf-8"))


def generate_api_key() -> Tuple[str, str]:
    """Generate a new API key and its hash.

    Returns:
        A tuple of (raw_key, hashed_key).  The raw key is shown once to the user;
        only the hash is persisted.
    """
    raw = _KEY_PREFIX + secrets.token_urlsafe(_KEY_LENGTH)
    hashed = _hash_password(raw)
    return raw, hashed


def generate_public_api_key() -> Tuple[str, str]:
    """Generate a public (read-only) API key and its hash.

    Returns:
        A tuple of (raw_key, hashed_key).
    """
    raw = _PUBLIC_KEY_PREFIX + secrets.token_urlsafe(_KEY_LENGTH)
    hashed = _hash_password(raw)
    return raw, hashed


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    """Verify a raw API key against its stored hash."""
    return _verify_password(raw_key, hashed_key)


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """FastAPI dependency: extract API key from ``Authorization: Bearer <key>``
    header, look it up in the database, and return the owning tenant.

    Raises:
        HTTPException 401 if the key is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide an Authorization: Bearer <key> header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_key = credentials.credentials

    # Fetch all active (non-expired) keys and verify against each.
    # For large-scale deployments consider a key-prefix index instead.
    stmt = (
        select(ApiKey)
        .options(selectinload(ApiKey.tenant))
    )
    result = await db.execute(stmt)
    api_keys: list[ApiKey] = list(result.scalars().all())

    for api_key in api_keys:
        if api_key.is_expired:
            continue
        if verify_api_key(raw_key, api_key.key_hash):
            if api_key.key_type == "public":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Public keys cannot access admin endpoints.",
                )
            # Update last-used timestamp
            api_key.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return api_key.tenant

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_public_tenant(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Tenant, ApiKey]:
    """FastAPI dependency for public widget endpoints.

    Accepts both public and admin API keys.  Returns a (Tenant, ApiKey) tuple
    so callers can inspect the key record (e.g. to find the linked widget config).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_key = credentials.credentials

    stmt = select(ApiKey).options(selectinload(ApiKey.tenant))
    result = await db.execute(stmt)
    api_keys: list[ApiKey] = list(result.scalars().all())

    for api_key in api_keys:
        if api_key.is_expired:
            continue
        if verify_api_key(raw_key, api_key.key_hash):
            api_key.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return api_key.tenant, api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )
