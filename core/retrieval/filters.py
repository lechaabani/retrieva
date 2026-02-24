"""Metadata and permission filters for retrieval results."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.retrieval.engine import ScoredChunk

logger = logging.getLogger(__name__)


@dataclass
class MetadataFilter:
    """Declarative filter specification for chunk metadata.

    Supports filtering by source, date range, tags, document type,
    and arbitrary key-value matches.
    """

    source: str | None = None
    source_type: str | None = None
    tags: list[str] = field(default_factory=list)
    date_from: datetime | None = None
    date_to: datetime | None = None
    document_type: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)

    def matches(self, metadata: dict[str, Any]) -> bool:
        """Return True if the metadata satisfies all filter criteria."""
        if self.source and metadata.get("source") != self.source:
            return False

        if self.source_type and metadata.get("source_type") != self.source_type:
            return False

        if self.document_type and metadata.get("document_type") != self.document_type:
            return False

        if self.tags:
            chunk_tags = set(metadata.get("tags", []))
            if not set(self.tags).issubset(chunk_tags):
                return False

        if self.date_from or self.date_to:
            created = metadata.get("created_at") or metadata.get("date")
            if created:
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created)
                    except ValueError:
                        return False
                if self.date_from and created < self.date_from:
                    return False
                if self.date_to and created > self.date_to:
                    return False

        for key, expected in self.custom.items():
            if metadata.get(key) != expected:
                return False

        return True


@dataclass
class PermissionFilter:
    """Role-based access filter.

    Checks that the user's role is allowed to access a chunk based on
    its ``allowed_roles`` metadata field.
    """

    user_role: str
    user_id: str | None = None

    def is_allowed(self, metadata: dict[str, Any]) -> bool:
        """Return True if the user has permission to access this chunk.

        Access rules:
        - If chunk has no ``allowed_roles``, it is public (allowed).
        - If ``allowed_roles`` is present, user_role must be in the list.
        - If ``owner_id`` matches user_id, access is always granted.
        """
        # Owner always has access
        if self.user_id and metadata.get("owner_id") == self.user_id:
            return True

        allowed_roles = metadata.get("allowed_roles")
        if not allowed_roles:
            return True

        if isinstance(allowed_roles, list):
            return self.user_role in allowed_roles
        return self.user_role == allowed_roles


def apply_filters(
    chunks: list[ScoredChunk],
    metadata_filter: MetadataFilter | None = None,
    permission_filter: PermissionFilter | None = None,
) -> list[ScoredChunk]:
    """Apply metadata and permission filters to a list of scored chunks.

    Args:
        chunks: Chunks to filter.
        metadata_filter: Optional metadata-based filter.
        permission_filter: Optional role-based access filter.

    Returns:
        Filtered list of chunks that match all criteria.
    """
    result: list[ScoredChunk] = []
    filtered_count = 0

    for chunk in chunks:
        meta = chunk.metadata

        if metadata_filter and not metadata_filter.matches(meta):
            filtered_count += 1
            continue

        if permission_filter and not permission_filter.is_allowed(meta):
            filtered_count += 1
            continue

        result.append(chunk)

    if filtered_count > 0:
        logger.debug("Filtered out %d of %d chunks", filtered_count, len(chunks))

    return result
