"""Connector source CRUD and sync trigger endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.connector_source import ConnectorSource
from api.models.tenant import Tenant

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sources"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConnectorSourceCreate(BaseModel):
    """Payload for creating a connector source."""

    name: str = Field(..., max_length=255)
    connector_type: str = Field(..., max_length=100, description="e.g. s3, confluence, github")
    config: dict = Field(default_factory=dict, description="Connector-specific configuration")
    sync_enabled: bool = Field(default=False)
    sync_interval_minutes: int = Field(default=360, ge=1, le=44640)


class ConnectorSourceUpdate(BaseModel):
    """Payload for updating a connector source."""

    name: Optional[str] = Field(default=None, max_length=255)
    connector_type: Optional[str] = Field(default=None, max_length=100)
    config: Optional[dict] = None
    sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(default=None, ge=1, le=44640)


class ConnectorSourceResponse(BaseModel):
    """Serialised connector source returned by the API."""

    id: UUID
    tenant_id: UUID
    name: str
    connector_type: str
    config: dict
    sync_enabled: bool
    sync_interval_minutes: int
    last_synced_at: Optional[str] = None
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class SyncTriggerResponse(BaseModel):
    """Response when triggering a manual sync."""

    message: str
    task_id: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    """Response for a connection test."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/sources",
    response_model=list[ConnectorSourceResponse],
    summary="List Connector Sources",
    description="List all connector sources for the current tenant.",
)
async def list_sources(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[ConnectorSourceResponse]:
    """Return all connector sources belonging to the tenant."""
    result = await db.execute(
        select(ConnectorSource)
        .where(ConnectorSource.tenant_id == tenant.id)
        .order_by(ConnectorSource.created_at.desc())
    )
    sources = result.scalars().all()
    return [
        ConnectorSourceResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            name=s.name,
            connector_type=s.connector_type,
            config=s.config or {},
            sync_enabled=s.sync_enabled,
            sync_interval_minutes=s.sync_interval_minutes,
            last_synced_at=s.last_synced_at.isoformat() if s.last_synced_at else None,
            status=s.status,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]


@router.post(
    "/sources",
    response_model=ConnectorSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Connector Source",
    description="Register a new external data source for syncing.",
)
async def create_source(
    payload: ConnectorSourceCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ConnectorSourceResponse:
    """Create a new connector source."""
    source = ConnectorSource(
        tenant_id=tenant.id,
        name=payload.name,
        connector_type=payload.connector_type,
        config=payload.config,
        sync_enabled=payload.sync_enabled,
        sync_interval_minutes=payload.sync_interval_minutes,
    )
    db.add(source)
    await db.flush()

    return ConnectorSourceResponse(
        id=source.id,
        tenant_id=source.tenant_id,
        name=source.name,
        connector_type=source.connector_type,
        config=source.config or {},
        sync_enabled=source.sync_enabled,
        sync_interval_minutes=source.sync_interval_minutes,
        last_synced_at=None,
        status=source.status,
        created_at=source.created_at.isoformat(),
    )


@router.put(
    "/sources/{source_id}",
    response_model=ConnectorSourceResponse,
    summary="Update Connector Source",
    description="Update an existing connector source configuration.",
)
async def update_source(
    source_id: UUID,
    payload: ConnectorSourceUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ConnectorSourceResponse:
    """Update fields on a connector source."""
    result = await db.execute(
        select(ConnectorSource).where(
            ConnectorSource.id == source_id,
            ConnectorSource.tenant_id == tenant.id,
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector source '{source_id}' not found.",
        )

    if payload.name is not None:
        source.name = payload.name
    if payload.connector_type is not None:
        source.connector_type = payload.connector_type
    if payload.config is not None:
        source.config = payload.config
    if payload.sync_enabled is not None:
        source.sync_enabled = payload.sync_enabled
    if payload.sync_interval_minutes is not None:
        source.sync_interval_minutes = payload.sync_interval_minutes

    await db.flush()

    return ConnectorSourceResponse(
        id=source.id,
        tenant_id=source.tenant_id,
        name=source.name,
        connector_type=source.connector_type,
        config=source.config or {},
        sync_enabled=source.sync_enabled,
        sync_interval_minutes=source.sync_interval_minutes,
        last_synced_at=source.last_synced_at.isoformat() if source.last_synced_at else None,
        status=source.status,
        created_at=source.created_at.isoformat(),
    )


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Connector Source",
    description="Permanently delete a connector source.",
)
async def delete_source(
    source_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a connector source by ID."""
    result = await db.execute(
        select(ConnectorSource).where(
            ConnectorSource.id == source_id,
            ConnectorSource.tenant_id == tenant.id,
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector source '{source_id}' not found.",
        )

    await db.delete(source)
    await db.flush()


@router.post(
    "/sources/{source_id}/sync",
    response_model=SyncTriggerResponse,
    summary="Trigger Manual Sync",
    description="Immediately trigger a sync for the specified connector source.",
)
async def trigger_sync(
    source_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> SyncTriggerResponse:
    """Dispatch a sync_connector task for the given source."""
    result = await db.execute(
        select(ConnectorSource).where(
            ConnectorSource.id == source_id,
            ConnectorSource.tenant_id == tenant.id,
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector source '{source_id}' not found.",
        )

    if source.status == "syncing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source is already being synced.",
        )

    from workers.sync_worker import sync_connector

    task = sync_connector.apply_async(
        kwargs={
            "connector_id": str(source.id),
            "connector_type": source.connector_type,
            "config": {
                **(source.config or {}),
                "tenant_id": str(tenant.id),
            },
        },
        queue="sync",
    )

    return SyncTriggerResponse(
        message=f"Sync triggered for source '{source.name}'.",
        task_id=task.id,
    )


@router.post(
    "/sources/{source_id}/test",
    response_model=ConnectionTestResponse,
    summary="Test Connection",
    description="Test whether the connector can reach the configured data source.",
)
async def test_connection(
    source_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ConnectionTestResponse:
    """Instantiate the connector and call test_connection."""
    result = await db.execute(
        select(ConnectorSource).where(
            ConnectorSource.id == source_id,
            ConnectorSource.tenant_id == tenant.id,
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector source '{source_id}' not found.",
        )

    try:
        from core.connectors import get_connector

        connector = get_connector(
            source_type=source.connector_type,
            config=source.config or {},
        )
        success = await connector.test_connection()
        return ConnectionTestResponse(
            success=success,
            message="Connection successful." if success else "Connection test returned false.",
        )
    except Exception as exc:
        logger.warning("Connection test failed for source %s: %s", source_id, exc)
        return ConnectionTestResponse(
            success=False,
            message=f"Connection test failed: {exc}",
        )
