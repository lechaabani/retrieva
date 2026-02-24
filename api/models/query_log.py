"""QueryLog model for tracking RAG queries and analytics."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: uuid.UUID = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    question: str = Column(Text, nullable=False)
    answer: str = Column(Text, nullable=True)
    sources: list = Column(JSONB, nullable=False, default=list)
    confidence: float = Column(Float, nullable=True)
    tokens_used: int = Column(Integer, nullable=True)
    latency_ms: int = Column(Integer, nullable=True)
    user_context: dict = Column(JSONB, nullable=False, default=dict)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="query_logs")

    def __repr__(self) -> str:
        return f"<QueryLog(id={self.id}, question='{self.question[:50]}...')>"
