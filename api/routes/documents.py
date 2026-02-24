"""Document management endpoints (list, get, delete)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.chunk import Chunk
from api.models.collection import Collection
from api.models.document import Document, DocumentStatus
from api.models.tenant import Tenant
from api.schemas.document import DocumentList, DocumentResponse

router = APIRouter(tags=["Documents"])


@router.get(
    "/documents",
    response_model=DocumentList,
    summary="List Documents",
    description="Retrieve a paginated list of documents scoped to the current tenant.",
)
async def list_documents(
    collection: Optional[str] = Query(default=None, description="Filter by collection name"),
    doc_status: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> DocumentList:
    """List documents with optional collection and status filters."""
    # Base query scoped to tenant
    base = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id)
    )
    count_base = (
        select(func.count(Document.id))
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id)
    )

    # Apply filters
    if collection:
        base = base.where(Collection.name == collection)
        count_base = count_base.where(Collection.name == collection)

    if doc_status:
        try:
            status_enum = DocumentStatus(doc_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{doc_status}'. Valid: {[s.value for s in DocumentStatus]}.",
            )
        base = base.where(Document.status == status_enum)
        count_base = count_base.where(Document.status == status_enum)

    # Count
    total_result = await db.execute(count_base)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    stmt = base.order_by(Document.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    return DocumentList(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get Document",
    description="Retrieve a single document by its ID.",
)
async def get_document(
    document_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Fetch a document by ID, scoped to the current tenant."""
    stmt = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id, Document.id == document_id)
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    return DocumentResponse.model_validate(document)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
    description="Delete a document and all its associated chunks and vectors.",
)
async def delete_document(
    document_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document, its chunks, and the corresponding vectors from the store."""
    # Verify ownership
    stmt = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id, Document.id == document_id)
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Collect vector IDs before deleting chunks so we can clean up the vector store
    chunk_stmt = select(Chunk.vector_id).where(
        Chunk.document_id == document_id,
        Chunk.vector_id.isnot(None),
    )
    chunk_result = await db.execute(chunk_stmt)
    vector_ids = [row[0] for row in chunk_result.all()]

    # Remove vectors from the vector store
    if vector_ids:
        try:
            from core.vector_store import VectorStore

            vector_store = VectorStore()
            await vector_store.delete(vector_ids)
        except Exception:
            # Log but don't fail the request; orphan vectors are acceptable
            import logging

            logging.getLogger("retrieva.api").warning(
                "Failed to delete vectors for document %s", document_id
            )

    # Delete chunks and document (cascades handle chunks via FK)
    await db.delete(document)
    await db.flush()


@router.get(
    "/documents/{document_id}/chunks",
    summary="Get Document Chunks",
    description="Return all indexed chunks for a document with their metadata and scores.",
)
async def get_document_chunks(
    document_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the chunks stored for a document, including content and metadata."""
    # Verify document belongs to tenant
    stmt = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id, Document.id == document_id)
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Fetch chunks from the database
    chunks_stmt = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.position)
    )
    chunks_result = await db.execute(chunks_stmt)
    db_chunks = chunks_result.scalars().all()

    chunks = []
    for chunk in db_chunks:
        content = chunk.content or ""
        chunks.append({
            "index": chunk.position,
            "chunk_id": str(chunk.id),
            "content": content,
            "metadata": chunk.chunk_metadata or {},
            "word_count": len(content.split()),
            "vector_id": chunk.vector_id,
        })

    return {
        "document_id": str(doc.id),
        "title": doc.title,
        "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
        "chunks_count": doc.chunks_count,
        "collection_id": str(doc.collection_id),
        "chunks": chunks,
    }
