"""ApiKey model for tenant authentication."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: str = Column(String(255), nullable=False, unique=True, index=True)
    name: str = Column(String(255), nullable=False)
    key_type: str = Column(String(20), nullable=False, default="admin")
    permissions: dict = Column(JSONB, nullable=False, default=dict)
    last_used_at: datetime = Column(DateTime(timezone=True), nullable=True)
    expires_at: datetime = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}')>"
