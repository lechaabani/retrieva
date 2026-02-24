"""Celery tasks for data source synchronisation.

Handles periodic and on-demand sync of external data sources (S3, GDrive,
Confluence, etc.) by detecting new, updated, and deleted documents and
queuing the appropriate ingestion tasks.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from workers.celery_app import app
from workers.db import get_sync_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_connector(source_type: str, connector_config: dict[str, Any]):
    """Instantiate and return the appropriate connector for *source_type*."""
    from core.connectors import get_connector
    return get_connector(source_type=source_type, config=connector_config)


def _compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@app.task(
    bind=True,
    name="workers.sync_worker.sync_source",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    acks_late=True,
)
def sync_source(
    self,
    source_config: dict[str, Any],
    collection_id: str,
    tenant_id: str,
) -> dict[str, Any]:
    """Synchronise a single external data source with the platform.

    Pulls the current file listing from the connector, compares content
    hashes against existing documents, and queues ingestion tasks for new
    or updated items. Documents no longer present at the source are marked
    as deleted.

    Args:
        source_config: Connector-specific configuration including ``type``.
        collection_id: UUID of the target collection.
        tenant_id: UUID of the owning tenant.

    Returns:
        Summary dict with counts of new, updated, and deleted documents.
    """
    import asyncio
    from api.models.document import Document, DocumentStatus
    from workers.ingestion_worker import ingest_file, ingest_text

    source_type = source_config.get("type", "unknown")
    logger.info(
        "Starting sync: source_type=%s collection=%s tenant=%s",
        source_type, collection_id, tenant_id,
    )

    try:
        connector = _get_connector(source_type, source_config)

        # Pull current listing from the external source
        loop = asyncio.new_event_loop()
        try:
            remote_items = loop.run_until_complete(connector.list_documents())
        finally:
            loop.close()

        # Build a lookup of existing documents by source_id
        with get_sync_session() as session:
            existing_docs = (
                session.query(Document)
                .filter(
                    Document.collection_id == uuid.UUID(collection_id),
                    Document.source_connector == source_type,
                )
                .all()
            )
            existing_by_source_id: dict[str, Document] = {
                doc.source_id: doc for doc in existing_docs if doc.source_id
            }

        remote_source_ids: set[str] = set()
        new_count = 0
        updated_count = 0
        deleted_count = 0

        for item in remote_items:
            source_id = item.get("source_id", item.get("id", ""))
            remote_source_ids.add(source_id)

            content_hash = item.get("content_hash")
            if not content_hash and item.get("content"):
                content_hash = _compute_content_hash(item["content"])

            if source_id in existing_by_source_id:
                existing_doc = existing_by_source_id[source_id]
                # Skip if content is unchanged
                if existing_doc.content_hash and existing_doc.content_hash == content_hash:
                    continue

                # Content changed — re-ingest
                doc_id = str(existing_doc.id)
                updated_count += 1
                logger.info("Source changed, re-ingesting: source_id=%s", source_id)
            else:
                # New document — create a DB record
                doc_id = str(uuid.uuid4())
                new_count += 1
                with get_sync_session() as session:
                    new_doc = Document(
                        id=uuid.UUID(doc_id),
                        collection_id=uuid.UUID(collection_id),
                        source_connector=source_type,
                        source_id=source_id,
                        title=item.get("title", source_id),
                        content_hash=content_hash,
                        doc_metadata=item.get("metadata", {}),
                        status=DocumentStatus.PENDING,
                    )
                    session.add(new_doc)

            # Queue the appropriate ingestion task
            if item.get("file_path"):
                ingest_file.apply_async(
                    kwargs={
                        "document_id": doc_id,
                        "file_path": item["file_path"],
                        "collection_id": collection_id,
                        "config": source_config.get("ingestion_config", {}),
                    },
                    queue="ingestion",
                )
            elif item.get("content"):
                ingest_text.apply_async(
                    kwargs={
                        "document_id": doc_id,
                        "content": item["content"],
                        "title": item.get("title", source_id),
                        "collection_id": collection_id,
                        "config": source_config.get("ingestion_config", {}),
                    },
                    queue="ingestion",
                )

        # Mark documents that no longer exist at the source
        for source_id, doc in existing_by_source_id.items():
            if source_id not in remote_source_ids:
                deleted_count += 1
                logger.info(
                    "Document removed from source, marking deleted: source_id=%s doc=%s",
                    source_id, doc.id,
                )
                with get_sync_session() as session:
                    db_doc = session.get(Document, doc.id)
                    if db_doc:
                        db_doc.status = DocumentStatus.ERROR
                        meta = dict(db_doc.doc_metadata) if db_doc.doc_metadata else {}
                        meta["deleted_from_source"] = True
                        meta["deleted_at"] = datetime.now(timezone.utc).isoformat()
                        db_doc.doc_metadata = meta
                        session.add(db_doc)

        result = {
            "source_type": source_type,
            "collection_id": collection_id,
            "tenant_id": tenant_id,
            "new": new_count,
            "updated": updated_count,
            "deleted": deleted_count,
        }
        logger.info("Sync complete: %s", result)
        return result

    except (ConnectionError, TimeoutError):
        raise

    except Exception as exc:
        logger.error(
            "Sync failed: source_type=%s collection=%s error=%s",
            source_type, collection_id, exc, exc_info=True,
        )
        raise self.retry(exc=exc)


@app.task(
    bind=True,
    name="workers.sync_worker.sync_connector",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    acks_late=True,
)
def sync_connector(
    self,
    connector_id: str,
    connector_type: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Sync a single connector source by ID.

    Reads from the configured connector source, ingests new or changed
    content, and updates the last_sync timestamp.

    Args:
        connector_id: UUID of the ConnectorSource record.
        connector_type: The type of connector (e.g. "s3", "confluence").
        config: Connector-specific configuration dict.

    Returns:
        Summary dict with counts of new, updated, and deleted documents.
    """
    import asyncio
    from api.models.connector_source import ConnectorSource

    logger.info(
        "Starting connector sync: connector_id=%s type=%s",
        connector_id, connector_type,
    )

    # Mark as syncing
    with get_sync_session() as session:
        source = session.get(ConnectorSource, uuid.UUID(connector_id))
        if source is None:
            logger.error("ConnectorSource %s not found", connector_id)
            return {"connector_id": connector_id, "error": "Not found"}
        source.status = "syncing"
        session.add(source)

    try:
        connector = _get_connector(connector_type, config)

        loop = asyncio.new_event_loop()
        try:
            remote_items = loop.run_until_complete(connector.list_documents())
        finally:
            loop.close()

        # Determine collection_id from config or use a default
        collection_id = config.get("collection_id", "")
        if not collection_id:
            logger.warning(
                "No collection_id in connector config for %s; skipping ingestion",
                connector_id,
            )
            remote_items = []

        from api.models.document import Document, DocumentStatus
        from workers.ingestion_worker import ingest_file, ingest_text

        # Load existing documents for comparison
        with get_sync_session() as session:
            existing_docs = (
                session.query(Document)
                .filter(
                    Document.source_connector == connector_type,
                )
                .all()
            )
            existing_by_source_id = {
                doc.source_id: doc for doc in existing_docs if doc.source_id
            }

        new_count = 0
        updated_count = 0
        remote_source_ids: set[str] = set()

        for item in remote_items:
            source_id = item.get("source_id", item.get("id", ""))
            remote_source_ids.add(source_id)

            content_hash = item.get("content_hash")
            if not content_hash and item.get("content"):
                content_hash = _compute_content_hash(item["content"])

            if source_id in existing_by_source_id:
                existing_doc = existing_by_source_id[source_id]
                if existing_doc.content_hash and existing_doc.content_hash == content_hash:
                    continue
                doc_id = str(existing_doc.id)
                updated_count += 1
            else:
                doc_id = str(uuid.uuid4())
                new_count += 1
                with get_sync_session() as session:
                    new_doc = Document(
                        id=uuid.UUID(doc_id),
                        collection_id=uuid.UUID(collection_id) if collection_id else None,
                        source_connector=connector_type,
                        source_id=source_id,
                        title=item.get("title", source_id),
                        content_hash=content_hash,
                        doc_metadata=item.get("metadata", {}),
                        status=DocumentStatus.PENDING,
                    )
                    session.add(new_doc)

            if item.get("file_path"):
                ingest_file.apply_async(
                    kwargs={
                        "document_id": doc_id,
                        "file_path": item["file_path"],
                        "collection_id": collection_id,
                        "config": config.get("ingestion_config", {}),
                    },
                    queue="ingestion",
                )
            elif item.get("content"):
                ingest_text.apply_async(
                    kwargs={
                        "document_id": doc_id,
                        "content": item["content"],
                        "title": item.get("title", source_id),
                        "collection_id": collection_id,
                        "config": config.get("ingestion_config", {}),
                    },
                    queue="ingestion",
                )

        # Update last_synced_at and status
        with get_sync_session() as session:
            source = session.get(ConnectorSource, uuid.UUID(connector_id))
            if source:
                source.last_synced_at = datetime.now(timezone.utc)
                source.status = "idle"
                session.add(source)

        # Dispatch webhook
        try:
            from core.webhooks import WebhookDispatcher

            tenant_id = config.get("tenant_id")
            if tenant_id:
                dispatcher = WebhookDispatcher(tenant_id=tenant_id)
                dispatcher.dispatch_sync("connector_sync_completed", {
                    "connector_id": connector_id,
                    "connector_type": connector_type,
                    "new": new_count,
                    "updated": updated_count,
                })
        except Exception as wh_exc:
            logger.warning("Webhook dispatch failed (non-fatal): %s", wh_exc)

        result = {
            "connector_id": connector_id,
            "connector_type": connector_type,
            "new": new_count,
            "updated": updated_count,
        }
        logger.info("Connector sync complete: %s", result)
        return result

    except (ConnectionError, TimeoutError):
        raise

    except Exception as exc:
        # Mark as error
        with get_sync_session() as session:
            source = session.get(ConnectorSource, uuid.UUID(connector_id))
            if source:
                source.status = "error"
                session.add(source)
        logger.error(
            "Connector sync failed: id=%s error=%s",
            connector_id, exc, exc_info=True,
        )
        raise self.retry(exc=exc)


@app.task(
    name="workers.sync_worker.check_pending_syncs",
    acks_late=True,
)
def check_pending_syncs() -> dict[str, Any]:
    """Periodic beat task: check ConnectorSource records with sync_enabled=True.

    For each source whose sync interval has elapsed since last_synced_at,
    dispatch a sync_connector task.

    Returns:
        Summary dict with the number of sync tasks queued.
    """
    from api.models.connector_source import ConnectorSource

    logger.info("Checking for pending connector syncs")

    queued = 0

    with get_sync_session() as session:
        sources = (
            session.query(ConnectorSource)
            .filter(ConnectorSource.sync_enabled.is_(True))
            .all()
        )

        now = datetime.now(timezone.utc)

        for source in sources:
            # Check if interval has elapsed
            if source.last_synced_at:
                from datetime import timedelta

                next_sync = source.last_synced_at + timedelta(
                    minutes=source.sync_interval_minutes
                )
                if now < next_sync:
                    continue

            # Skip if already syncing
            if source.status == "syncing":
                continue

            sync_connector.apply_async(
                kwargs={
                    "connector_id": str(source.id),
                    "connector_type": source.connector_type,
                    "config": {
                        **(source.config or {}),
                        "tenant_id": str(source.tenant_id),
                    },
                },
                queue="sync",
            )
            queued += 1

    logger.info("Queued %d connector sync tasks", queued)
    return {"queued": queued}


@app.task(
    name="workers.sync_worker.sync_all_sources",
    acks_late=True,
)
def sync_all_sources(tenant_id: str) -> dict[str, Any]:
    """Queue sync tasks for all configured sources belonging to a tenant.

    Reads the tenant's collection configs and schedules ``sync_source``
    for each source that has ``sync_enabled`` set to true.

    Args:
        tenant_id: UUID of the tenant to sync.

    Returns:
        Summary dict with the number of sync tasks queued.
    """
    from api.models.tenant import Tenant
    from api.models.collection import Collection

    logger.info("Syncing all sources for tenant=%s", tenant_id)

    queued = 0

    with get_sync_session() as session:
        tenant = session.get(Tenant, uuid.UUID(tenant_id))
        if not tenant:
            logger.error("Tenant not found: %s", tenant_id)
            return {"tenant_id": tenant_id, "queued": 0, "error": "Tenant not found"}

        collections = (
            session.query(Collection)
            .filter(Collection.tenant_id == uuid.UUID(tenant_id))
            .all()
        )

        for collection in collections:
            col_config = collection.config or {}
            sources = col_config.get("sources", [])

            for source_cfg in sources:
                if not source_cfg.get("sync_enabled", False):
                    continue

                sync_source.apply_async(
                    kwargs={
                        "source_config": source_cfg,
                        "collection_id": str(collection.id),
                        "tenant_id": tenant_id,
                    },
                    queue="sync",
                )
                queued += 1

    logger.info("Queued %d sync tasks for tenant=%s", queued, tenant_id)
    return {"tenant_id": tenant_id, "queued": queued}


@app.task(
    name="workers.sync_worker.sync_all_sources_periodic",
    acks_late=True,
)
def sync_all_sources_periodic() -> dict[str, Any]:
    """Periodic beat task: sync all sources across all active tenants.

    Called by the Celery Beat scheduler at the configured interval.
    Loads all tenants and queues ``sync_all_sources`` for each one.

    Returns:
        Summary dict with the total number of tenants processed.
    """
    from api.models.tenant import Tenant

    logger.info("Periodic sync: scanning all tenants")

    tenant_count = 0

    with get_sync_session() as session:
        tenants = session.query(Tenant).all()

        for tenant in tenants:
            sync_all_sources.apply_async(
                kwargs={"tenant_id": str(tenant.id)},
                queue="sync",
            )
            tenant_count += 1

    logger.info("Periodic sync: queued sync for %d tenants", tenant_count)
    return {"tenants_processed": tenant_count}
