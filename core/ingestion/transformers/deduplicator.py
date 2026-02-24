"""Content deduplication transformer.

Computes a SHA-256 hash of the document text and skips documents that
have already been processed.  Maintains an in-process set of seen hashes
and optionally checks against the database.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from core.ingestion.transformers.base import BaseTransformer

logger = logging.getLogger(__name__)


class Deduplicator(BaseTransformer):
    """Skip documents whose content has already been seen.

    Uses a SHA-256 content hash.  Maintains a local set for within-batch
    deduplication and optionally checks against existing content hashes
    in the database.
    """

    name = "deduplicator"

    def __init__(self, check_database: bool = True) -> None:
        """
        Args:
            check_database: If True, also check the ``documents`` table
                for an existing content_hash match.
        """
        self.check_database = check_database
        self._seen_hashes: set[str] = set()

    def transform(
        self, text: str, metadata: dict[str, Any]
    ) -> tuple[str | None, dict[str, Any]]:
        """Return (None, metadata) if the content is a duplicate, signalling skip.

        Otherwise return the text unchanged with the content_hash added
        to metadata.
        """
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        metadata["content_hash"] = content_hash

        # In-batch dedup
        if content_hash in self._seen_hashes:
            logger.info("Duplicate content detected (in-batch): hash=%s", content_hash[:16])
            metadata["duplicate"] = True
            metadata["duplicate_reason"] = "in_batch"
            return None, metadata

        # Database dedup
        if self.check_database and self._hash_exists_in_db(content_hash):
            logger.info("Duplicate content detected (database): hash=%s", content_hash[:16])
            metadata["duplicate"] = True
            metadata["duplicate_reason"] = "database"
            return None, metadata

        self._seen_hashes.add(content_hash)
        return text, metadata

    def reset(self) -> None:
        """Clear the in-process seen set (e.g. between batches)."""
        self._seen_hashes.clear()

    @staticmethod
    def _hash_exists_in_db(content_hash: str) -> bool:
        """Check if a document with the given content hash exists in the database.

        Uses a synchronous session suitable for both async and sync callers.
        """
        try:
            from workers.db import get_sync_session
            from api.models.document import Document

            with get_sync_session() as session:
                existing = (
                    session.query(Document)
                    .filter(Document.content_hash == content_hash)
                    .first()
                )
                return existing is not None
        except Exception as exc:
            logger.debug("Database dedup check failed (non-fatal): %s", exc)
            return False
