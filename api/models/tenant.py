"""Tenant model representing an organization or workspace."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    name: str = Column(String(255), nullable=False)
    slug: str = Column(String(255), unique=True, nullable=False, index=True)
    config: dict = Column(JSONB, nullable=False, default=dict)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    collections = relationship("Collection", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    widget_configs = relationship("WidgetConfig", back_populates="tenant", cascade="all, delete-orphan")
    subscription = relationship("Subscription", uselist=False, back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, slug='{self.slug}')>"
