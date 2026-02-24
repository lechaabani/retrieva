"""Chunk model representing a text chunk derived from a document."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    document_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: str = Column(Text, nullable=False)
    position: int = Column(Integer, nullable=False)
    chunk_metadata: dict = Column("metadata", JSONB, nullable=False, default=dict)
    vector_id: str = Column(String(255), nullable=True, index=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")
    collection = relationship("Collection", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, position={self.position})>"
