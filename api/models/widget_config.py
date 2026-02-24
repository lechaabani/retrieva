"""WidgetConfig model for embeddable widget configurations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: str = Column(String(255), nullable=False)
    widget_type: str = Column(String(50), nullable=False)  # "chatbot" or "search"
    collection_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    config: dict = Column(JSONB, nullable=False, default=dict)
    public_api_key_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: bool = Column(Boolean, nullable=False, default=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="widget_configs")
    collection = relationship("Collection")
    public_api_key = relationship("ApiKey")

    def __repr__(self) -> str:
        return f"<WidgetConfig(id={self.id}, name='{self.name}', type='{self.widget_type}')>"
