"""ConnectorSource model for external data source configurations with sync scheduling."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class ConnectorSource(Base):
    __tablename__ = "connector_sources"

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
    connector_type: str = Column(String(100), nullable=False)
    config: dict = Column(JSONB, nullable=False, default=dict)
    sync_enabled: bool = Column(Boolean, nullable=False, default=False)
    sync_interval_minutes: int = Column(Integer, nullable=False, default=360)
    last_synced_at: datetime = Column(DateTime(timezone=True), nullable=True)
    status: str = Column(String(50), nullable=False, default="idle")
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tenant = relationship("Tenant", backref="connector_sources")

    def __repr__(self) -> str:
        return (
            f"<ConnectorSource(id={self.id}, name='{self.name}', "
            f"type='{self.connector_type}', sync_enabled={self.sync_enabled})>"
        )
