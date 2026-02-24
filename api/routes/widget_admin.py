"""Admin CRUD endpoints for widget configurations."""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import generate_public_api_key, get_current_tenant
from api.database import get_db
from api.models.api_key import ApiKey
from api.models.collection import Collection
from api.models.tenant import Tenant
from api.models.widget_config import WidgetConfig
from api.schemas.widget import (
    WidgetConfigCreate,
    WidgetConfigResponse,
    WidgetConfigUpdate,
    WidgetEmbedResponse,
)

router = APIRouter(prefix="/admin/widgets", tags=["Widgets"])


async def _get_widget_or_404(
    widget_id: UUID, tenant: Tenant, db: AsyncSession
) -> WidgetConfig:
    stmt = select(WidgetConfig).where(
        WidgetConfig.id == widget_id,
        WidgetConfig.tenant_id == tenant.id,
    )
    result = await db.execute(stmt)
    widget = result.scalar_one_or_none()
    if widget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    return widget


@router.get("", response_model=list[WidgetConfigResponse])
async def list_widgets(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[WidgetConfigResponse]:
    stmt = select(WidgetConfig).where(WidgetConfig.tenant_id == tenant.id).order_by(WidgetConfig.created_at.desc())
    result = await db.execute(stmt)
    widgets = list(result.scalars().all())
    return [WidgetConfigResponse.model_validate(w) for w in widgets]


@router.post("", response_model=WidgetConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    body: WidgetConfigCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigResponse:
    # Validate collection belongs to tenant if provided
    if body.collection_id:
        stmt = select(Collection).where(
            Collection.id == body.collection_id,
            Collection.tenant_id == tenant.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    # Generate a public API key for this widget
    raw_key, hashed_key = generate_public_api_key()
    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hashed_key,
        name=f"Widget: {body.name}",
        key_type="public",
        permissions={"scopes": ["query", "search"]},
    )
    db.add(api_key)
    await db.flush()

    widget = WidgetConfig(
        tenant_id=tenant.id,
        name=body.name,
        widget_type=body.widget_type,
        collection_id=body.collection_id,
        config=body.config,
        public_api_key_id=api_key.id,
        is_active=body.is_active,
    )
    db.add(widget)
    await db.flush()

    resp = WidgetConfigResponse.model_validate(widget)
    resp.raw_public_key = raw_key
    return resp


@router.get("/{widget_id}", response_model=WidgetConfigResponse)
async def get_widget(
    widget_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigResponse:
    widget = await _get_widget_or_404(widget_id, tenant, db)
    return WidgetConfigResponse.model_validate(widget)


@router.put("/{widget_id}", response_model=WidgetConfigResponse)
async def update_widget(
    widget_id: UUID,
    body: WidgetConfigUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigResponse:
    widget = await _get_widget_or_404(widget_id, tenant, db)

    if body.name is not None:
        widget.name = body.name
    if body.collection_id is not None:
        # Validate collection
        stmt = select(Collection).where(
            Collection.id == body.collection_id,
            Collection.tenant_id == tenant.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
        widget.collection_id = body.collection_id
    if body.config is not None:
        # Merge config
        merged = {**widget.config, **body.config}
        widget.config = merged
    if body.is_active is not None:
        widget.is_active = body.is_active

    await db.flush()
    return WidgetConfigResponse.model_validate(widget)


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    widget = await _get_widget_or_404(widget_id, tenant, db)
    # Delete the associated public API key
    if widget.public_api_key_id:
        stmt = select(ApiKey).where(ApiKey.id == widget.public_api_key_id)
        result = await db.execute(stmt)
        key = result.scalar_one_or_none()
        if key:
            await db.delete(key)
    await db.delete(widget)
    await db.flush()


@router.get("/{widget_id}/embed", response_model=WidgetEmbedResponse)
async def get_embed_code(
    widget_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WidgetEmbedResponse:
    widget = await _get_widget_or_404(widget_id, tenant, db)

    public_url = os.environ.get("RETRIEVA_PUBLIC_URL", "http://localhost:8000")
    key_prefix = ""
    if widget.public_api_key_id:
        stmt = select(ApiKey).where(ApiKey.id == widget.public_api_key_id)
        result = await db.execute(stmt)
        key = result.scalar_one_or_none()
        if key:
            key_prefix = key.name  # We store the prefix hint in the key name

    embed_code = (
        f'<script src="{public_url}/widget/{widget.widget_type}.js"\n'
        f'        data-widget-id="{widget.id}"\n'
        f'        data-api="{public_url}"></script>'
    )

    return WidgetEmbedResponse(
        widget_id=widget.id,
        embed_code=embed_code,
        public_key_prefix=key_prefix,
    )
