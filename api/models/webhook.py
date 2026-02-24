"""Webhook model for event notification subscriptions."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from api.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: str = Column(String(2048), nullable=False)
    events: list[str] = Column(ARRAY(String(100)), nullable=False, default=list)
    active: bool = Column(Boolean, nullable=False, default=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tenant = relationship("Tenant", backref="webhooks")

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, url='{self.url}', active={self.active})>"
