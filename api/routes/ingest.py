"""Document ingestion endpoints (file upload, raw text, URL)."""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.middleware.rate_limit import limiter, DEFAULT_INGEST_LIMIT
from api.models.collection import Collection
from api.models.document import Document, DocumentStatus
from api.models.tenant import Tenant
from api.schemas.ingest import IngestResponse, IngestTextRequest, IngestUrlRequest
from sqlalchemy import select

router = APIRouter(tags=["Ingestion"])

ALLOWED_FILE_TYPES = {"pdf", "docx", "xlsx", "txt", "md", "csv"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/markdown",
    "text/csv",
}


async def _resolve_collection_by_name(
    name: str, tenant: Tenant, db: AsyncSession
) -> Collection:
    """Look up a collection by name scoped to the tenant."""
    stmt = select(Collection).where(
        Collection.tenant_id == tenant.id,
        Collection.name == name,
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' not found.",
        )
    return collection


def _validate_file_extension(filename: str) -> str:
    """Return the lowercase file extension or raise 400."""
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid extension.",
        )
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not supported. Allowed types: {', '.join(sorted(ALLOWED_FILE_TYPES))}.",
        )
    return ext


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest File",
    description="Upload a file for ingestion into a collection. Supported formats: PDF, DOCX, XLSX, TXT, MD, CSV.",
)
@limiter.limit(DEFAULT_INGEST_LIMIT)
async def ingest_file(
    request: Request,
    file: UploadFile = File(..., description="The file to ingest"),
    collection: str = Form(..., description="Target collection name"),
    metadata: Optional[str] = Form(default=None, description="JSON metadata string"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Accept a file upload, validate it, create a document record, and queue ingestion."""
    ext = _validate_file_extension(file.filename or "")

    col = await _resolve_collection_by_name(collection, tenant, db)

    # Create document record in pending state
    doc = Document(
        collection_id=col.id,
        source_connector="file_upload",
        source_id=file.filename,
        title=file.filename or "Untitled",
        doc_metadata=_parse_metadata(metadata),
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.flush()

    # Save file to disk then queue Celery task
    upload_dir = os.path.join("/data/documents", str(col.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc.id}.{ext}")
    file_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    from workers.ingestion_worker import ingest_file as ingest_file_task

    ingest_file_task.delay(
        document_id=str(doc.id),
        file_path=file_path,
        collection_id=str(col.id),
    )

    return IngestResponse(
        document_id=doc.id,
        status="processing",
        chunks_count=0,
        message=f"File '{file.filename}' queued for ingestion.",
    )


@router.post(
    "/ingest/text",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest Text",
    description="Submit raw text content for ingestion into a collection.",
)
@limiter.limit(DEFAULT_INGEST_LIMIT)
async def ingest_text(
    request: Request,
    body: IngestTextRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Accept raw text, create a document record, and queue ingestion."""
    col = await _resolve_collection_by_name(body.collection, tenant, db)

    doc = Document(
        collection_id=col.id,
        source_connector="text_input",
        title=body.title,
        doc_metadata=body.metadata,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.flush()

    from workers.ingestion_worker import ingest_text as ingest_text_task

    ingest_text_task.delay(
        document_id=str(doc.id),
        content=body.content,
        title=body.title,
        collection_id=str(col.id),
    )

    return IngestResponse(
        document_id=doc.id,
        status="processing",
        chunks_count=0,
        message=f"Text document '{body.title}' queued for ingestion.",
    )


@router.post(
    "/ingest/url",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest URL",
    description="Crawl a URL and ingest its content into a collection.",
)
@limiter.limit(DEFAULT_INGEST_LIMIT)
async def ingest_url(
    request: Request,
    body: IngestUrlRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Accept a URL, create a document record, and queue crawl + ingestion."""
    col = await _resolve_collection_by_name(body.collection, tenant, db)

    doc = Document(
        collection_id=col.id,
        source_connector="url_crawl",
        source_id=str(body.url),
        title=str(body.url),
        doc_metadata=body.metadata,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.flush()

    from workers.ingestion_worker import ingest_url as ingest_url_task

    ingest_url_task.delay(
        document_id=str(doc.id),
        url=str(body.url),
        collection_id=str(col.id),
    )

    return IngestResponse(
        document_id=doc.id,
        status="processing",
        chunks_count=0,
        message=f"URL '{body.url}' queued for crawling and ingestion.",
    )


def _parse_metadata(raw: Optional[str]) -> dict:
    """Safely parse optional JSON metadata from a form field."""
    if not raw:
        return {}
    import json

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata must be a JSON object.",
            )
        return parsed
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in metadata: {exc}",
        )
