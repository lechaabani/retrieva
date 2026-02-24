"""Subscription model for tenant billing and usage limits."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    stripe_customer_id: str = Column(String(255), nullable=True)
    stripe_subscription_id: str = Column(String(255), nullable=True)
    plan: str = Column(String(50), nullable=False, default="community")
    status: str = Column(String(50), nullable=False, default="active")
    current_period_start: datetime = Column(DateTime(timezone=True), nullable=True)
    current_period_end: datetime = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: bool = Column(Boolean, nullable=False, default=False)

    # Usage limits
    max_documents: int = Column(Integer, nullable=False, default=100)
    max_queries_per_month: int = Column(Integer, nullable=False, default=1000)
    max_collections: int = Column(Integer, nullable=False, default=3)
    max_widgets: int = Column(Integer, nullable=False, default=0)

    # Usage tracking
    queries_this_month: int = Column(Integer, nullable=False, default=0)
    queries_month_reset: datetime = Column(DateTime(timezone=True), nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, plan='{self.plan}', status='{self.status}')>"
