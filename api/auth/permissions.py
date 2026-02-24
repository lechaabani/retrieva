"""Permission service for role-based collection access control.

When permissions are enabled (config.permissions.enabled), users can only
access collections their role is explicitly granted access to.
Admin roles (config.permissions.admin_roles) bypass all permission checks.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.collection import Collection
from api.models.collection_permission import CollectionPermission
from api.models.tenant import Tenant
from api.models.user import User
from core.config import get_config

logger = logging.getLogger(__name__)


def is_admin(user: User) -> bool:
    """Check if the user has an admin role."""
    cfg = get_config()
    return user.role in cfg.permissions.admin_roles


async def check_collection_access(
    user: User,
    collection: Collection,
    db: AsyncSession,
) -> bool:
    """Check whether *user* is allowed to access *collection*.

    Returns True if:
    - Permissions are disabled globally, OR
    - The user has an admin role, OR
    - A CollectionPermission row exists for the user's role + collection.
    """
    cfg = get_config()

    # If permissions are disabled, everyone can access everything
    if not cfg.permissions.enabled:
        return True

    # Admin roles bypass
    if is_admin(user):
        return True

    # Check explicit permission
    stmt = select(CollectionPermission).where(
        CollectionPermission.collection_id == collection.id,
        CollectionPermission.role == user.role,
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()

    return perm is not None


async def get_accessible_collection_ids(
    user: User,
    tenant: Tenant,
    db: AsyncSession,
) -> list[UUID] | None:
    """Return list of collection IDs the user can access, or None if unrestricted.

    Returns None when permissions are disabled or user is admin (meaning all
    collections are accessible).
    """
    cfg = get_config()

    if not cfg.permissions.enabled:
        return None  # No restriction

    if is_admin(user):
        return None  # No restriction

    # Get all collection IDs that the user's role can access within this tenant
    stmt = (
        select(CollectionPermission.collection_id)
        .join(Collection, CollectionPermission.collection_id == Collection.id)
        .where(
            Collection.tenant_id == tenant.id,
            CollectionPermission.role == user.role,
        )
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


def require_collection_access():
    """FastAPI dependency that verifies the current user can access
    the requested collection. Use in conjunction with get_current_user.

    Usage in endpoint:
        async def endpoint(
            user: User = Depends(get_current_user),
            access_check: None = Depends(require_collection_access()),
        ):
    """

    async def _check(
        user: User,
        collection: Collection,
        db: AsyncSession,
    ) -> None:
        has_access = await check_collection_access(user, collection, db)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' does not have access to this collection.",
            )

    return _check
