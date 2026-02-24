"""Admin endpoints: analytics, user management, API keys, logs, webhooks, health."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import generate_api_key, get_current_tenant, _hash_password, _verify_password
from api.auth.jwt import create_access_token, get_current_user, require_role
from api.database import get_db
from api.models.api_key import ApiKey
from api.models.query_log import QueryLog
from api.models.tenant import Tenant
from api.models.collection import Collection
from api.models.collection_permission import CollectionPermission
from api.models.user import User
from api.schemas.admin import (
    AnalyticsBucket,
    AnalyticsResponse,
    QueryLogList,
    QueryLogResponse,
    TenantConfig,
    WebhookConfig,
    WebhookResponse,
)
from api.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    LoginResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(tags=["Admin"])


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get(
    "/admin/analytics",
    response_model=AnalyticsResponse,
    summary="Query Analytics",
    description="Retrieve aggregated query analytics for the current tenant.",
)
async def get_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Number of past days to analyze"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    """Return aggregated query stats (count, avg latency, avg confidence) over a date range."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    base_filter = [
        QueryLog.tenant_id == tenant.id,
        QueryLog.created_at >= period_start,
    ]

    # Totals
    totals = await db.execute(
        select(
            func.count(QueryLog.id),
            func.coalesce(func.avg(QueryLog.latency_ms), 0),
            func.coalesce(func.avg(QueryLog.confidence), 0),
            func.coalesce(func.sum(QueryLog.tokens_used), 0),
        ).where(*base_filter)
    )
    row = totals.one()
    total_queries = row[0]
    avg_latency = float(row[1])
    avg_confidence = float(row[2])
    total_tokens = int(row[3])

    # Daily buckets
    daily = await db.execute(
        select(
            func.date_trunc("day", QueryLog.created_at).label("bucket"),
            func.count(QueryLog.id),
            func.coalesce(func.avg(QueryLog.latency_ms), 0),
            func.coalesce(func.avg(QueryLog.confidence), 0),
        )
        .where(*base_filter)
        .group_by("bucket")
        .order_by("bucket")
    )
    buckets = [
        AnalyticsBucket(
            date=r[0].strftime("%Y-%m-%d"),
            query_count=r[1],
            avg_latency_ms=float(r[2]),
            avg_confidence=float(r[3]),
        )
        for r in daily.all()
    ]

    return AnalyticsResponse(
        total_queries=total_queries,
        avg_latency_ms=avg_latency,
        avg_confidence=avg_confidence,
        total_tokens_used=total_tokens,
        period_start=period_start,
        period_end=now,
        buckets=buckets,
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get(
    "/admin/users",
    response_model=list[UserResponse],
    summary="List Users",
    description="List all users in the current tenant. Admin only.",
    dependencies=[Depends(require_role("admin"))],
)
async def list_users(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """Return all users belonging to the tenant."""
    result = await db.execute(
        select(User)
        .where(User.tenant_id == tenant.id)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user account within the current tenant.",
)
async def create_user(
    payload: UserCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a user with a hashed password."""
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{payload.email}' is already registered.",
        )

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=_hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.flush()

    return UserResponse.model_validate(user)


@router.put(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update a user's role or email.",
    dependencies=[Depends(require_role("admin"))],
)
async def update_user(
    user_id: UUID,
    payload: dict,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update user fields (email, role, password)."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if "email" in payload:
        existing = await db.execute(
            select(User).where(User.email == payload["email"], User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken.")
        user.email = payload["email"]
    if "role" in payload:
        if payload["role"] not in ("admin", "member", "viewer"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")
        user.role = payload["role"]
    if "password" in payload:
        user.password_hash = _hash_password(payload["password"])

    await db.flush()
    return UserResponse.model_validate(user)


@router.delete(
    "/admin/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Permanently delete a user account.",
    dependencies=[Depends(require_role("admin"))],
)
async def delete_user(
    user_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    await db.delete(user)
    await db.flush()


@router.post(
    "/admin/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate a user and return a JWT access token, session API key, and user info.",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Verify credentials, issue a JWT, and generate a session API key."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    )

    # Fetch tenant name
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one()

    # Generate a short-lived session API key for the dashboard
    raw_key, hashed_key = generate_api_key()
    session_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hashed_key,
        name="Dashboard Session",
        permissions=["read", "write", "admin"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session_key)
    await db.flush()

    return LoginResponse(
        access_token=token,
        api_key=raw_key,
        user={"id": str(user.id), "email": user.email, "role": user.role},
        tenant_name=tenant.name,
    )


@router.post(
    "/admin/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Account",
    description="Create a new tenant with a user account. Self-service registration.",
)
async def register(
    payload: dict,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Self-service registration: create tenant + admin user + API key."""
    import re

    # Validate required fields
    email = payload.get("email")
    password = payload.get("password")
    name = payload.get("name", "")
    org_name = payload.get("org_name", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This email is already registered.")

    # Create tenant
    org = org_name or email.split("@")[0]
    slug = re.sub(r"[^a-z0-9\-]", "", org.lower().replace(" ", "-")) or "tenant"

    # Ensure unique slug
    slug_check = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if slug_check.scalar_one_or_none():
        import uuid
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    tenant = Tenant(
        name=org,
        slug=slug,
        config={
            "plan": "free",
            "registered_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=_hash_password(password),
        role="admin",
    )
    db.add(user)
    await db.flush()

    # Create API key
    raw_key, hashed_key = generate_api_key()
    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hashed_key,
        name="Default Admin Key",
        permissions=["read", "write", "admin"],
    )
    db.add(api_key)
    await db.flush()

    # Create JWT
    token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(tenant.id), "role": user.role}
    )

    return LoginResponse(
        access_token=token,
        api_key=raw_key,
        user={"id": str(user.id), "email": user.email, "role": user.role},
        tenant_name=tenant.name,
    )


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------

@router.post(
    "/admin/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate API Key",
    description="Generate a new API key for the current tenant.",
)
async def create_api_key(
    payload: ApiKeyCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    """Generate a new API key. The raw key is returned only once."""
    raw_key, hashed_key = generate_api_key()

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hashed_key,
        name=payload.name,
        permissions=payload.permissions,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=raw_key[:12],
        permissions=api_key.permissions,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        raw_key=raw_key,
    )


@router.get(
    "/admin/api-keys",
    response_model=list[ApiKeyResponse],
    summary="List API Keys",
    description="List all API keys for the current tenant.",
)
async def list_api_keys(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    """Return metadata for all API keys (hashes are never exposed)."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == tenant.id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_hash[:8],  # not the actual key, just an identifier
            permissions=k.permissions,
            created_at=k.created_at,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
        )
        for k in keys
    ]


@router.delete(
    "/admin/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API Key",
    description="Permanently revoke an API key.",
)
async def revoke_api_key(
    key_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an API key by ID."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == tenant.id)
    )
    key = result.scalar_one_or_none()

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_id}' not found.",
        )

    await db.delete(key)
    await db.flush()


# ---------------------------------------------------------------------------
# Query logs
# ---------------------------------------------------------------------------

@router.get(
    "/admin/logs",
    response_model=QueryLogList,
    summary="Query Logs",
    description="Retrieve paginated query logs for the current tenant.",
)
async def get_query_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    collection_id: Optional[UUID] = Query(default=None, description="Filter by collection"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> QueryLogList:
    """Paginated query log listing."""
    base_filter = [QueryLog.tenant_id == tenant.id]
    if collection_id:
        base_filter.append(QueryLog.collection_id == collection_id)

    total_result = await db.execute(
        select(func.count(QueryLog.id)).where(*base_filter)
    )
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(QueryLog)
        .where(*base_filter)
        .order_by(QueryLog.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return QueryLogList(
        logs=[QueryLogResponse.model_validate(log) for log in logs],
        page=page,
        per_page=per_page,
        total=total,
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@router.get(
    "/admin/settings",
    summary="Get Platform Settings",
    description="Retrieve the platform settings for the current tenant.",
)
async def get_settings(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the tenant's platform settings stored in tenant.config."""
    defaults = {
        "platform_name": tenant.name,
        "default_language": "fr",
        "default_persona": "",
        "retrieval_strategy": "hybrid",
        "vector_weight": 0.7,
        "default_top_k": 5,
        "reranking": False,
        "generation_provider": "openai",
        "generation_model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_events": [],
    }
    config = tenant.config or {}
    return {**defaults, **config.get("settings", {})}


@router.put(
    "/admin/settings",
    summary="Update Platform Settings",
    description="Update the platform settings for the current tenant.",
)
async def update_settings(
    payload: dict,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Merge provided settings into tenant.config['settings']."""
    config = dict(tenant.config) if tenant.config else {}
    existing_settings = config.get("settings", {})
    existing_settings.update(payload)
    config["settings"] = existing_settings
    tenant.config = config

    # SQLAlchemy needs to know the JSONB changed
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(tenant, "config")
    await db.flush()

    defaults = {
        "platform_name": tenant.name,
        "default_language": "fr",
        "default_persona": "",
        "retrieval_strategy": "hybrid",
        "vector_weight": 0.7,
        "default_top_k": 5,
        "reranking": False,
        "generation_provider": "openai",
        "generation_model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_events": [],
    }
    return {**defaults, **config["settings"]}


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

@router.get(
    "/admin/webhooks",
    response_model=list[WebhookResponse],
    summary="List Webhooks",
    description="List all registered webhooks for the current tenant.",
)
async def list_webhooks(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookResponse]:
    """Return all webhook configurations for the tenant."""
    from api.models.webhook import Webhook

    result = await db.execute(
        select(Webhook)
        .where(Webhook.tenant_id == tenant.id)
        .order_by(Webhook.created_at.desc())
    )
    hooks = result.scalars().all()
    return [WebhookResponse.model_validate(h) for h in hooks]


@router.post(
    "/admin/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure Webhook",
    description="Register a new webhook endpoint for event notifications.",
)
async def create_webhook(
    payload: WebhookConfig,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """Create a webhook configuration in the dedicated webhooks table."""
    from api.models.webhook import Webhook

    webhook = Webhook(
        tenant_id=tenant.id,
        url=str(payload.url),
        events=payload.events,
        active=payload.active,
    )
    db.add(webhook)
    await db.flush()

    return WebhookResponse.model_validate(webhook)


@router.delete(
    "/admin/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Webhook",
    description="Permanently delete a webhook subscription.",
)
async def delete_webhook(
    webhook_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a webhook by ID."""
    from api.models.webhook import Webhook

    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if webhook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook '{webhook_id}' not found.",
        )

    await db.delete(webhook)
    await db.flush()


# ---------------------------------------------------------------------------
# Permissions (RBAC)
# ---------------------------------------------------------------------------

@router.get(
    "/admin/permissions",
    summary="List Collection Permissions",
    description="List all role-to-collection permission mappings for the current tenant.",
    dependencies=[Depends(require_role("admin"))],
)
async def list_permissions(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return all permission mappings within the tenant."""
    stmt = (
        select(CollectionPermission)
        .join(Collection, CollectionPermission.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id)
        .order_by(CollectionPermission.created_at.desc())
    )
    result = await db.execute(stmt)
    perms = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "collection_id": str(p.collection_id),
            "role": p.role,
            "granted_by": str(p.granted_by) if p.granted_by else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in perms
    ]


@router.post(
    "/admin/permissions",
    status_code=status.HTTP_201_CREATED,
    summary="Grant Collection Access",
    description="Grant a role access to a specific collection.",
    dependencies=[Depends(require_role("admin"))],
)
async def grant_permission(
    collection_id: UUID,
    role: str,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a permission mapping for a role to access a collection."""
    # Verify collection belongs to tenant
    coll_result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.tenant_id == tenant.id,
        )
    )
    collection = coll_result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found.",
        )

    # Check for existing permission
    existing = await db.execute(
        select(CollectionPermission).where(
            CollectionPermission.collection_id == collection_id,
            CollectionPermission.role == role,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{role}' already has access to this collection.",
        )

    perm = CollectionPermission(
        collection_id=collection_id,
        role=role,
        granted_by=user.id,
    )
    db.add(perm)
    await db.flush()

    return {
        "id": str(perm.id),
        "collection_id": str(perm.collection_id),
        "role": perm.role,
        "granted_by": str(perm.granted_by),
    }


@router.delete(
    "/admin/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke Collection Access",
    description="Remove a role's access to a collection.",
    dependencies=[Depends(require_role("admin"))],
)
async def revoke_permission(
    permission_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a permission mapping."""
    stmt = (
        select(CollectionPermission)
        .join(Collection, CollectionPermission.collection_id == Collection.id)
        .where(
            CollectionPermission.id == permission_id,
            Collection.tenant_id == tenant.id,
        )
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()
    if perm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found.",
        )
    await db.delete(perm)
    await db.flush()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    summary="Detailed Health Check",
    description="Returns detailed health status of API and all dependencies.",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Check all services and return detailed health report."""
    import time
    import os

    components = {}
    overall_healthy = True

    # Database check
    try:
        start = time.perf_counter()
        await db.execute(select(func.now()))
        latency = (time.perf_counter() - start) * 1000
        components["database"] = {"status": "healthy", "latency_ms": round(latency, 1)}
    except Exception as exc:
        components["database"] = {"status": "unhealthy", "error": str(exc)[:200]}
        overall_healthy = False

    # Qdrant check
    try:
        import httpx
        start = time.perf_counter()
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{qdrant_url}/collections")
            resp.raise_for_status()
        latency = (time.perf_counter() - start) * 1000
        collection_count = len(resp.json().get("result", {}).get("collections", []))
        components["qdrant"] = {"status": "healthy", "latency_ms": round(latency, 1), "collections": collection_count}
    except Exception as exc:
        components["qdrant"] = {"status": "unhealthy", "error": str(exc)[:200]}
        overall_healthy = False

    # Redis check
    try:
        import redis.asyncio as aioredis
        start = time.perf_counter()
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        r = aioredis.from_url(redis_url, decode_responses=True)
        await r.ping()
        info = await r.info("memory")
        await r.aclose()
        latency = (time.perf_counter() - start) * 1000
        components["redis"] = {
            "status": "healthy",
            "latency_ms": round(latency, 1),
            "memory_used": info.get("used_memory_human", "?"),
        }
    except Exception as exc:
        components["redis"] = {"status": "unhealthy", "error": str(exc)[:200]}
        overall_healthy = False

    # LLM Provider check (from tenant config)
    tenant = None
    try:
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if tenant and tenant.config:
            gen_provider = tenant.config.get("generation_provider", "unknown")
            gen_key = tenant.config.get("generation_api_key", "")
            has_key = bool(gen_key)
            components["llm_provider"] = {
                "status": "configured" if has_key else "not_configured",
                "provider": gen_provider,
                "has_api_key": has_key,
            }
        else:
            components["llm_provider"] = {"status": "not_configured"}
    except Exception:
        components["llm_provider"] = {"status": "unknown"}

    # Embedding Provider check
    try:
        if tenant and tenant.config:
            emb_provider = tenant.config.get("embedding_provider", "unknown")
            emb_key = tenant.config.get("embedding_api_key", "")
            has_key = bool(emb_key)
            components["embedding_provider"] = {
                "status": "configured" if has_key else "not_configured",
                "provider": emb_provider,
                "has_api_key": has_key,
            }
        else:
            components["embedding_provider"] = {"status": "not_configured"}
    except Exception:
        components["embedding_provider"] = {"status": "unknown"}

    # Celery worker check
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        r = aioredis.from_url(redis_url, decode_responses=True)
        workers = await r.keys("celery-task-meta-*")
        await r.aclose()
        components["celery_worker"] = {
            "status": "healthy",
            "task_results_count": len(workers) if workers else 0,
        }
    except Exception:
        components["celery_worker"] = {"status": "unknown"}

    # Document/collection stats
    try:
        from api.models.document import Document
        doc_count = await db.execute(select(func.count(Document.id)))
        coll_count = await db.execute(select(func.count(Collection.id)))
        components["data"] = {
            "documents": doc_count.scalar() or 0,
            "collections": coll_count.scalar() or 0,
        }
    except Exception:
        pass

    return {
        "status": "ok" if overall_healthy else "degraded",
        "version": "0.1.0",
        "components": components,
    }


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------

@router.get(
    "/admin/export",
    summary="Export Platform Config",
    description="Export all platform configuration as a JSON file.",
)
async def export_config(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export tenant config, collections, widgets, and webhooks as portable JSON."""
    from api.models.widget_config import WidgetConfig
    from api.models.webhook import Webhook

    # Collections
    collections_result = await db.execute(
        select(Collection).where(Collection.tenant_id == tenant.id)
    )
    collections = [
        {
            "name": c.name,
            "description": c.description,
            "config": c.config,
        }
        for c in collections_result.scalars().all()
    ]

    # Widgets
    widgets_result = await db.execute(
        select(WidgetConfig).where(WidgetConfig.tenant_id == tenant.id)
    )
    widgets = [
        {
            "name": w.name,
            "widget_type": w.widget_type,
            "config": w.config,
            "is_active": w.is_active,
        }
        for w in widgets_result.scalars().all()
    ]

    # Webhooks
    webhooks_result = await db.execute(
        select(Webhook).where(Webhook.tenant_id == tenant.id)
    )
    webhooks = [
        {
            "url": w.url,
            "events": w.events,
            "active": w.active,
        }
        for w in webhooks_result.scalars().all()
    ]

    # Settings
    settings = (tenant.config or {}).get("settings", {})

    return {
        "version": "1.0",
        "platform_name": tenant.name,
        "settings": settings,
        "provider_config": {
            "embedding_provider": (tenant.config or {}).get("embedding_provider"),
            "generation_provider": (tenant.config or {}).get("generation_provider"),
            "generation_model": (tenant.config or {}).get("generation_model"),
        },
        "collections": collections,
        "widgets": widgets,
        "webhooks": webhooks,
    }


@router.post(
    "/admin/import",
    summary="Import Platform Config",
    description="Import platform configuration from a JSON export.",
)
async def import_config(
    payload: dict,
    merge: bool = Query(default=True, description="Merge with existing config (true) or replace (false)"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Import a previously exported config. Creates collections and widgets that don't exist yet."""
    from api.models.widget_config import WidgetConfig
    from api.models.webhook import Webhook
    from sqlalchemy.orm.attributes import flag_modified

    imported = {"settings": False, "collections": 0, "widgets": 0, "webhooks": 0}

    # Import settings
    if "settings" in payload:
        config = dict(tenant.config) if tenant.config else {}
        if merge:
            existing = config.get("settings", {})
            existing.update(payload["settings"])
            config["settings"] = existing
        else:
            config["settings"] = payload["settings"]
        tenant.config = config
        flag_modified(tenant, "config")
        imported["settings"] = True

    # Import provider config (only if provided and no existing keys — never overwrite API keys)
    if "provider_config" in payload:
        config = dict(tenant.config) if tenant.config else {}
        for key in ["embedding_provider", "generation_provider", "generation_model"]:
            if payload["provider_config"].get(key):
                config[key] = payload["provider_config"][key]
        tenant.config = config
        flag_modified(tenant, "config")

    # Import collections
    if "collections" in payload:
        existing_collections = await db.execute(
            select(Collection.name).where(Collection.tenant_id == tenant.id)
        )
        existing_names = {r[0] for r in existing_collections.all()}

        for coll_data in payload["collections"]:
            if coll_data["name"] not in existing_names:
                coll = Collection(
                    tenant_id=tenant.id,
                    name=coll_data["name"],
                    description=coll_data.get("description"),
                    config=coll_data.get("config", {}),
                )
                db.add(coll)
                imported["collections"] += 1

    # Import widgets
    if "widgets" in payload:
        existing_widgets = await db.execute(
            select(WidgetConfig.name).where(WidgetConfig.tenant_id == tenant.id)
        )
        existing_names = {r[0] for r in existing_widgets.all()}

        for widget_data in payload["widgets"]:
            if widget_data["name"] not in existing_names:
                widget = WidgetConfig(
                    tenant_id=tenant.id,
                    name=widget_data["name"],
                    widget_type=widget_data.get("widget_type", "chatbot"),
                    config=widget_data.get("config", {}),
                    is_active=widget_data.get("is_active", True),
                )
                db.add(widget)
                imported["widgets"] += 1

    # Import webhooks
    if "webhooks" in payload:
        existing_webhooks = await db.execute(
            select(Webhook.url).where(Webhook.tenant_id == tenant.id)
        )
        existing_urls = {r[0] for r in existing_webhooks.all()}

        for wh_data in payload["webhooks"]:
            if wh_data["url"] not in existing_urls:
                webhook = Webhook(
                    tenant_id=tenant.id,
                    url=wh_data["url"],
                    events=wh_data.get("events", []),
                    active=wh_data.get("active", True),
                )
                db.add(webhook)
                imported["webhooks"] += 1

    await db.flush()

    return {
        "message": "Import completed",
        "imported": imported,
    }
