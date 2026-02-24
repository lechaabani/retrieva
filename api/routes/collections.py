"""Collection management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.chunk import Chunk
from api.models.collection import Collection
from api.models.document import Document
from api.models.tenant import Tenant
from api.schemas.collection import (
    CollectionCreate,
    CollectionList,
    CollectionResponse,
    CollectionUpdate,
)

router = APIRouter(tags=["Collections"])


def _collection_response(col: Collection, doc_count: int = 0, chunk_count: int = 0) -> CollectionResponse:
    """Build a CollectionResponse with computed stats."""
    return CollectionResponse(
        id=col.id,
        tenant_id=col.tenant_id,
        name=col.name,
        description=col.description,
        config=col.config,
        created_at=col.created_at,
        documents_count=doc_count,
        chunks_count=chunk_count,
    )


@router.get(
    "/collections",
    response_model=CollectionList,
    summary="List Collections",
    description="Retrieve all collections for the current tenant.",
)
async def list_collections(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> CollectionList:
    """List collections with document and chunk counts."""
    count_result = await db.execute(
        select(func.count(Collection.id)).where(Collection.tenant_id == tenant.id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    stmt = (
        select(Collection)
        .where(Collection.tenant_id == tenant.id)
        .order_by(Collection.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    collections = result.scalars().all()

    items = []
    for col in collections:
        doc_count_res = await db.execute(
            select(func.count(Document.id)).where(Document.collection_id == col.id)
        )
        chunk_count_res = await db.execute(
            select(func.count(Chunk.id)).where(Chunk.collection_id == col.id)
        )
        items.append(
            _collection_response(
                col,
                doc_count=doc_count_res.scalar() or 0,
                chunk_count=chunk_count_res.scalar() or 0,
            )
        )

    return CollectionList(collections=items, page=page, per_page=per_page, total=total)


@router.post(
    "/collections",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Collection",
    description="Create a new document collection within the current tenant.",
)
async def create_collection(
    payload: CollectionCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Create a new collection. Name must be unique within the tenant."""
    # Check for duplicate name
    existing = await db.execute(
        select(Collection).where(
            Collection.tenant_id == tenant.id,
            Collection.name == payload.name,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Collection '{payload.name}' already exists.",
        )

    col = Collection(
        tenant_id=tenant.id,
        name=payload.name,
        description=payload.description,
        config=payload.config,
    )
    db.add(col)
    await db.flush()

    return _collection_response(col)


@router.get(
    "/collections/{collection_id}",
    response_model=CollectionResponse,
    summary="Get Collection",
    description="Retrieve a collection with document and chunk statistics.",
)
async def get_collection(
    collection_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Fetch a single collection by ID with aggregated stats."""
    stmt = select(Collection).where(
        Collection.id == collection_id,
        Collection.tenant_id == tenant.id,
    )
    result = await db.execute(stmt)
    col = result.scalar_one_or_none()

    if col is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found.",
        )

    doc_count = (
        await db.execute(
            select(func.count(Document.id)).where(Document.collection_id == col.id)
        )
    ).scalar() or 0

    chunk_count = (
        await db.execute(
            select(func.count(Chunk.id)).where(Chunk.collection_id == col.id)
        )
    ).scalar() or 0

    return _collection_response(col, doc_count=doc_count, chunk_count=chunk_count)


@router.put(
    "/collections/{collection_id}",
    response_model=CollectionResponse,
    summary="Update Collection",
    description="Update a collection's name, description, or configuration.",
)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Partially update an existing collection."""
    stmt = select(Collection).where(
        Collection.id == collection_id,
        Collection.tenant_id == tenant.id,
    )
    result = await db.execute(stmt)
    col = result.scalar_one_or_none()

    if col is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found.",
        )

    # Check name uniqueness if name is being changed
    if payload.name is not None and payload.name != col.name:
        dup = await db.execute(
            select(Collection).where(
                Collection.tenant_id == tenant.id,
                Collection.name == payload.name,
            )
        )
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Collection '{payload.name}' already exists.",
            )
        col.name = payload.name

    if payload.description is not None:
        col.description = payload.description
    if payload.config is not None:
        col.config = payload.config

    await db.flush()

    return _collection_response(col)


@router.delete(
    "/collections/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Collection",
    description="Delete a collection and all its documents, chunks, and vectors.",
)
async def delete_collection(
    collection_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a collection and cascade-delete all child documents and chunks."""
    stmt = select(Collection).where(
        Collection.id == collection_id,
        Collection.tenant_id == tenant.id,
    )
    result = await db.execute(stmt)
    col = result.scalar_one_or_none()

    if col is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found.",
        )

    # Clean up vectors from the vector store
    chunk_stmt = select(Chunk.vector_id).where(
        Chunk.collection_id == collection_id,
        Chunk.vector_id.isnot(None),
    )
    chunk_result = await db.execute(chunk_stmt)
    vector_ids = [row[0] for row in chunk_result.all()]

    if vector_ids:
        try:
            from core.vector_store import VectorStore

            vector_store = VectorStore()
            await vector_store.delete(vector_ids)
        except Exception:
            import logging

            logging.getLogger("retrieva.api").warning(
                "Failed to delete vectors for collection %s", collection_id
            )

    await db.delete(col)
    await db.flush()
