"""Document model representing an ingested document."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from api.database import Base


class DocumentStatus(str, enum.Enum):
    """Processing status of a document."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class Document(Base):
    __tablename__ = "documents"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    collection_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_connector: str = Column(String(100), nullable=False)
    source_id: str = Column(String(512), nullable=True)
    title: str = Column(String(512), nullable=False)
    content_hash: str = Column(String(64), nullable=True, index=True)
    doc_metadata: dict = Column("metadata", JSONB, nullable=False, default=dict)
    status: DocumentStatus = Column(
        Enum(DocumentStatus, name="document_status", create_type=True),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    chunks_count: int = Column(Integer, nullable=False, default=0)
    indexed_at: datetime = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', status={self.status})>"
