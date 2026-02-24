"""Collection-level permission model for role-based access control.

Maps user roles to collections they can access. When permissions are enabled,
users can only query/search collections they have explicit access to.
Admin roles bypass permission checks.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.database import Base


class CollectionPermission(Base):
    """Grants a role access to a specific collection."""

    __tablename__ = "collection_permissions"
    __table_args__ = (
        UniqueConstraint("collection_id", "role", name="uq_collection_role"),
    )

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    collection_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: str = Column(String(50), nullable=False, index=True)
    granted_by: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    collection = relationship("Collection")

    def __repr__(self) -> str:
        return f"<CollectionPermission(collection={self.collection_id}, role='{self.role}')>"
