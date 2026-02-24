"""Vector store wrapper around Qdrant for collection management and search."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from core.exceptions import CollectionNotFoundError, VectorStoreError

logger = logging.getLogger(__name__)


class VectorStore:
    """Async-compatible wrapper around the Qdrant vector database.

    Provides methods for collection lifecycle management, vector upsert,
    similarity search, scrolling, and deletion.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc_port: int = 6334,
        api_key: str = "",
        prefer_grpc: bool = True,
        collection_prefix: str = "retrieva_",
    ) -> None:
        """
        Args:
            host: Qdrant server hostname.
            port: Qdrant HTTP port.
            grpc_port: Qdrant gRPC port.
            api_key: Qdrant API key (for Qdrant Cloud).
            prefer_grpc: Whether to use gRPC transport.
            collection_prefix: Prefix for all collection names.
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.api_key = api_key
        self.prefer_grpc = prefer_grpc
        self.collection_prefix = collection_prefix
        self._client = None

    def _get_client(self):
        """Lazily initialise the Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient

                kwargs: dict[str, Any] = {
                    "host": self.host,
                    "port": self.port,
                    "grpc_port": self.grpc_port,
                    "prefer_grpc": self.prefer_grpc,
                }
                if self.api_key:
                    kwargs["api_key"] = self.api_key

                self._client = QdrantClient(**kwargs)
                logger.info("Connected to Qdrant at %s:%d", self.host, self.port)
            except ImportError:
                raise VectorStoreError(
                    "qdrant-client is required: pip install qdrant-client"
                )
            except Exception as exc:
                raise VectorStoreError(f"Failed to connect to Qdrant: {exc}") from exc
        return self._client

    def _full_name(self, collection_name: str) -> str:
        """Apply the collection prefix."""
        if collection_name.startswith(self.collection_prefix):
            return collection_name
        return f"{self.collection_prefix}{collection_name}"

    # ── Collection management ──────────────────────────────────────────────

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "cosine",
        on_disk: bool = False,
    ) -> None:
        """Create a new vector collection.

        Args:
            collection_name: Logical collection name (prefix is auto-applied).
            vector_size: Dimensionality of the vectors.
            distance: Distance metric ("cosine", "euclid", "dot").
            on_disk: Whether to store vectors on disk.

        Raises:
            VectorStoreError: On creation failure.
        """
        from qdrant_client.models import Distance, VectorParams

        distance_map = {
            "cosine": Distance.COSINE,
            "euclid": Distance.EUCLID,
            "dot": Distance.DOT,
        }

        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            collections = client.get_collections().collections
            existing = {c.name for c in collections}
            if full_name in existing:
                logger.info("Collection %s already exists", full_name)
                return

            client.create_collection(
                collection_name=full_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE),
                    on_disk=on_disk,
                ),
            )
            logger.info("Created collection %s (dim=%d, dist=%s)", full_name, vector_size, distance)

        except Exception as exc:
            raise VectorStoreError(f"Failed to create collection: {exc}") from exc

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a vector collection.

        Args:
            collection_name: Collection to delete.

        Raises:
            VectorStoreError: On deletion failure.
        """
        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            client.delete_collection(collection_name=full_name)
            logger.info("Deleted collection %s", full_name)
        except Exception as exc:
            raise VectorStoreError(f"Failed to delete collection: {exc}") from exc

    # ── Vector operations ──────────────────────────────────────────────────

    async def upsert_vectors(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Insert or update vectors in a collection.

        Args:
            collection_name: Target collection.
            ids: Unique identifiers for each vector.
            vectors: Embedding vectors.
            payloads: Optional metadata payloads, one per vector.

        Raises:
            VectorStoreError: On upsert failure.
        """
        from qdrant_client.models import PointStruct

        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            points = []
            for i, (vid, vector) in enumerate(zip(ids, vectors)):
                # Use a deterministic UUID from the string ID
                try:
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, vid))
                except Exception:
                    point_id = vid

                payload = payloads[i] if payloads and i < len(payloads) else {}
                payload["_original_id"] = vid

                points.append(
                    PointStruct(id=point_id, vector=vector, payload=payload)
                )

            # Batch upsert in groups of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                client.upsert(collection_name=full_name, points=batch)

            logger.debug("Upserted %d vectors into %s", len(points), full_name)

        except Exception as exc:
            raise VectorStoreError(f"Failed to upsert vectors: {exc}") from exc

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: Optional[dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            collection_name: Collection to search.
            query_vector: Query embedding vector.
            limit: Maximum number of results.
            filters: Optional Qdrant filter conditions.
            score_threshold: Minimum similarity score.

        Returns:
            List of result dicts with "id", "score", and payload fields.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            VectorStoreError: On search failure.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            results = client.search(
                collection_name=full_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
            )

            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    **(hit.payload or {}),
                }
                for hit in results
            ]

        except Exception as exc:
            error_str = str(exc).lower()
            if "not found" in error_str or "doesn't exist" in error_str:
                raise CollectionNotFoundError(f"Collection {full_name} not found") from exc
            raise VectorStoreError(f"Search failed: {exc}") from exc

    async def scroll(
        self,
        collection_name: str,
        limit: int = 10000,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Scroll through all points in a collection.

        Used primarily for building BM25 keyword indices.

        Args:
            collection_name: Collection to scroll.
            limit: Maximum number of points to return.
            filters: Optional filter conditions.

        Returns:
            List of payload dicts for all matching points.
        """
        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            all_points: list[dict[str, Any]] = []
            offset = None

            while len(all_points) < limit:
                batch_limit = min(100, limit - len(all_points))
                points, next_offset = client.scroll(
                    collection_name=full_name,
                    limit=batch_limit,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in points:
                    payload = point.payload or {}
                    payload["id"] = str(point.id)
                    all_points.append(payload)

                if next_offset is None or not points:
                    break
                offset = next_offset

            return all_points

        except Exception as exc:
            raise VectorStoreError(f"Scroll failed: {exc}") from exc

    async def delete(
        self,
        collection_name: str,
        ids: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> None:
        """Delete vectors from a collection by ID or filter.

        Args:
            collection_name: Target collection.
            ids: Specific point IDs to delete.
            filters: Filter conditions for bulk deletion.

        Raises:
            VectorStoreError: On deletion failure.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointIdsList

        full_name = self._full_name(collection_name)
        client = self._get_client()

        try:
            if ids:
                # Convert string IDs to the UUID format used during upsert
                point_ids = []
                for vid in ids:
                    try:
                        point_ids.append(str(uuid.uuid5(uuid.NAMESPACE_DNS, vid)))
                    except Exception:
                        point_ids.append(vid)

                client.delete(
                    collection_name=full_name,
                    points_selector=PointIdsList(points=point_ids),
                )
                logger.debug("Deleted %d points from %s", len(ids), full_name)

            elif filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                qdrant_filter = Filter(must=conditions)
                client.delete(
                    collection_name=full_name,
                    points_selector=qdrant_filter,
                )
                logger.debug("Deleted points by filter from %s", full_name)

            else:
                raise VectorStoreError("Provide either ids or filters for deletion")

        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"Delete failed: {exc}") from exc
