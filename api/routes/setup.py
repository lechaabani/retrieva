"""First-time setup endpoints (no auth required)."""

import os
import re
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import generate_api_key, _hash_password
from api.database import get_db
from api.models.api_key import ApiKey
from api.models.collection import Collection
from api.models.tenant import Tenant
from api.models.user import User
from api.schemas.setup import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    SetupInitRequest,
    SetupInitResponse,
    SetupStatusResponse,
)

router = APIRouter(tags=["Setup"])


def _slugify(value: str) -> str:
    """Convert a platform name into a URL-safe slug."""
    slug = value.lower().strip().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug or "retrieva"


# ---------------------------------------------------------------------------
# GET /setup/status
# ---------------------------------------------------------------------------

@router.get(
    "/setup/status",
    response_model=SetupStatusResponse,
    summary="Check Setup Status",
    description="Return whether the platform needs first-time setup.",
)
async def setup_status(
    db: AsyncSession = Depends(get_db),
) -> SetupStatusResponse:
    """Count tenants in the database and report whether setup is needed."""
    result = await db.execute(select(func.count(Tenant.id)))
    count = result.scalar() or 0
    return SetupStatusResponse(needs_setup=count == 0)


# ---------------------------------------------------------------------------
# POST /setup/init
# ---------------------------------------------------------------------------

@router.post(
    "/setup/init",
    response_model=SetupInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialise Platform",
    description="Run first-time setup: create the initial tenant, admin user, API key, and optional collection.",
)
async def setup_init(
    payload: SetupInitRequest,
    db: AsyncSession = Depends(get_db),
) -> SetupInitResponse:
    """Perform the one-time platform bootstrap.

    This endpoint is only usable when no tenants exist. Once a tenant has been
    created, subsequent calls will return 409 Conflict.
    """
    # Guard: setup already completed
    existing = await db.execute(select(func.count(Tenant.id)))
    if (existing.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup has already been completed. Platform is initialised.",
        )

    # 1. Create tenant
    # Default model per provider
    gen_model = payload.generation_model
    if not gen_model:
        gen_model = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-20250514",
            "google": "gemini-2.0-flash",
            "ollama": "llama3",
        }.get(payload.generation_provider, "gpt-4o-mini")

    tenant = Tenant(
        name=payload.platform_name,
        slug=_slugify(payload.platform_name),
        config={
            "embedding_provider": payload.embedding_provider,
            "embedding_api_key": payload.embedding_api_key,
            "generation_provider": payload.generation_provider,
            "generation_model": gen_model,
            "generation_api_key": payload.generation_api_key,
        },
    )
    db.add(tenant)
    await db.flush()

    # 2. Create admin user
    user = User(
        tenant_id=tenant.id,
        email=payload.admin_email,
        password_hash=_hash_password(payload.admin_password),
        role="admin",
    )
    db.add(user)
    await db.flush()

    # 3. Generate default API key
    raw_key, hashed_key = generate_api_key()
    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hashed_key,
        name="Default Admin Key",
        permissions=["read", "write", "admin"],
    )
    db.add(api_key)
    await db.flush()

    # 4. Optionally create a collection
    collection_id = None
    if payload.collection_name:
        collection = Collection(
            tenant_id=tenant.id,
            name=payload.collection_name,
        )
        db.add(collection)
        await db.flush()
        collection_id = str(collection.id)

    return SetupInitResponse(
        tenant_id=str(tenant.id),
        user_id=str(user.id),
        api_key=raw_key,
        collection_id=collection_id,
        message="Setup complete",
    )


# ---------------------------------------------------------------------------
# POST /setup/test-connection
# ---------------------------------------------------------------------------

async def _test_embedding(provider: str | None, api_key: str | None, base_url: str | None) -> dict:
    """Test connectivity to an embedding provider."""
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "openai":
            url = base_url or "https://api.openai.com/v1/embeddings"
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "text-embedding-3-small", "input": "test"},
            )
            resp.raise_for_status()
            return {"model": "text-embedding-3-small", "dimensions": len(resp.json()["data"][0]["embedding"])}
        elif provider == "ollama":
            url = base_url or "http://localhost:11434"
            resp = await client.get(f"{url}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            return {"available_models": models}
        elif provider == "cohere":
            url = base_url or "https://api.cohere.ai/v1/embed"
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"texts": ["test"], "model": "embed-multilingual-v3.0", "input_type": "search_document"},
            )
            resp.raise_for_status()
            return {"model": "embed-multilingual-v3.0"}
        elif provider == "google":
            url = base_url or f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
            resp = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"content": {"parts": [{"text": "test"}]}},
            )
            resp.raise_for_status()
            return {"model": "text-embedding-004"}
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")


async def _test_generation(provider: str | None, api_key: str | None, base_url: str | None) -> dict:
    """Test connectivity to a generation (LLM) provider."""
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "openai":
            url = base_url or "https://api.openai.com/v1/chat/completions"
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 3,
                },
            )
            resp.raise_for_status()
            return {"model": "gpt-4o-mini"}
        elif provider == "anthropic":
            url = base_url or "https://api.anthropic.com/v1/messages"
            resp = await client.post(
                url,
                headers={
                    "x-api-key": api_key or "",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 3,
                    "messages": [{"role": "user", "content": "Say OK"}],
                },
            )
            resp.raise_for_status()
            return {"model": "claude-sonnet-4-20250514"}
        elif provider == "ollama":
            url = base_url or "http://localhost:11434"
            resp = await client.post(
                f"{url}/api/generate",
                json={"model": "llama3", "prompt": "Say OK", "stream": False},
            )
            resp.raise_for_status()
            return {"model": resp.json().get("model", "llama3")}
        elif provider == "google":
            url = base_url or f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            resp = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "Say OK"}]}]},
            )
            resp.raise_for_status()
            return {"model": "gemini-2.0-flash"}
        else:
            raise ValueError(f"Unknown generation provider: {provider}")


async def _test_qdrant() -> dict:
    """Test connectivity to Qdrant vector database."""
    timeout = httpx.Timeout(10.0)
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(f"{qdrant_url}/collections")
        resp.raise_for_status()
        collections = resp.json().get("result", {}).get("collections", [])
        return {"collections_count": len(collections)}


async def _test_redis() -> dict:
    """Test connectivity to Redis."""
    import redis.asyncio as aioredis

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    r = aioredis.from_url(redis_url, socket_connect_timeout=10)
    try:
        pong = await r.ping()
        info = await r.info("server")
        return {"ping": pong, "redis_version": info.get("redis_version", "unknown")}
    finally:
        await r.aclose()


async def _test_database(db: AsyncSession) -> dict:
    """Test database connectivity with a simple query."""
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"select_1": value}


@router.post(
    "/setup/test-connection",
    response_model=ConnectionTestResponse,
    summary="Test External Connection",
    description="Test connectivity to an external service (embedding, generation, qdrant, redis, database).",
)
async def test_connection(
    payload: ConnectionTestRequest,
    db: AsyncSession = Depends(get_db),
) -> ConnectionTestResponse:
    """Test a connection to an external service and return status + latency."""
    start = time.perf_counter()
    try:
        if payload.service == "embedding":
            details = await _test_embedding(payload.provider, payload.api_key, payload.base_url)
        elif payload.service == "generation":
            details = await _test_generation(payload.provider, payload.api_key, payload.base_url)
        elif payload.service == "qdrant":
            details = await _test_qdrant()
        elif payload.service == "redis":
            details = await _test_redis()
        elif payload.service == "database":
            details = await _test_database(db)
        else:
            raise ValueError(f"Unknown service: {payload.service}")

        latency_ms = (time.perf_counter() - start) * 1000
        return ConnectionTestResponse(
            service=payload.service,
            status="ok",
            latency_ms=round(latency_ms, 1),
            message=f"Connection to {payload.service} successful",
            details=details,
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return ConnectionTestResponse(
            service=payload.service,
            status="error",
            latency_ms=round(latency_ms, 1),
            message=str(exc),
            details=None,
        )
