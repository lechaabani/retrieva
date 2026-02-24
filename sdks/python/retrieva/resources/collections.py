"""Collections resource for CRUD operations on collections."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, List, Optional

from retrieva.types import Collection


class CollectionsResource:
    """Handles collection CRUD via the sync client."""

    def __init__(self, request_fn: Callable[..., Dict[str, Any]]) -> None:
        self._request = request_fn

    def list(self) -> List[Collection]:
        """List all collections.

        Returns:
            A list of Collection objects.
        """
        data = self._request("GET", "/api/v1/collections")
        items = data if isinstance(data, list) else data.get("collections", data.get("items", []))
        return [Collection.from_dict(c) for c in items]

    def create(
        self,
        *,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Collection:
        """Create a new collection.

        Args:
            name: The name of the collection.
            description: An optional description.
            metadata: Optional metadata for the collection.

        Returns:
            The newly created Collection.
        """
        payload: Dict[str, Any] = {"name": name, "description": description}
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._request("POST", "/api/v1/collections", json=payload)
        return Collection.from_dict(data)

    def get(self, collection_id: str) -> Collection:
        """Get a collection by ID.

        Args:
            collection_id: The UUID of the collection.

        Returns:
            The requested Collection.
        """
        data = self._request("GET", f"/api/v1/collections/{collection_id}")
        return Collection.from_dict(data)

    def update(
        self,
        collection_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Collection:
        """Update a collection.

        Args:
            collection_id: The UUID of the collection to update.
            name: New name for the collection.
            description: New description for the collection.
            metadata: New metadata for the collection.

        Returns:
            The updated Collection.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._request("PUT", f"/api/v1/collections/{collection_id}", json=payload)
        return Collection.from_dict(data)

    def delete(self, collection_id: str) -> None:
        """Delete a collection.

        Args:
            collection_id: The UUID of the collection to delete.
        """
        self._request("DELETE", f"/api/v1/collections/{collection_id}")


class AsyncCollectionsResource:
    """Handles collection CRUD via the async client."""

    def __init__(
        self,
        request_fn: Callable[..., Coroutine[Any, Any, Dict[str, Any]]],
    ) -> None:
        self._request = request_fn

    async def list(self) -> List[Collection]:
        """List all collections.

        Returns:
            A list of Collection objects.
        """
        data = await self._request("GET", "/api/v1/collections")
        items = data if isinstance(data, list) else data.get("collections", data.get("items", []))
        return [Collection.from_dict(c) for c in items]

    async def create(
        self,
        *,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Collection:
        """Create a new collection.

        Args:
            name: The name of the collection.
            description: An optional description.
            metadata: Optional metadata for the collection.

        Returns:
            The newly created Collection.
        """
        payload: Dict[str, Any] = {"name": name, "description": description}
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request("POST", "/api/v1/collections", json=payload)
        return Collection.from_dict(data)

    async def get(self, collection_id: str) -> Collection:
        """Get a collection by ID.

        Args:
            collection_id: The UUID of the collection.

        Returns:
            The requested Collection.
        """
        data = await self._request("GET", f"/api/v1/collections/{collection_id}")
        return Collection.from_dict(data)

    async def update(
        self,
        collection_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Collection:
        """Update a collection.

        Args:
            collection_id: The UUID of the collection to update.
            name: New name for the collection.
            description: New description for the collection.
            metadata: New metadata for the collection.

        Returns:
            The updated Collection.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request(
            "PUT", f"/api/v1/collections/{collection_id}", json=payload
        )
        return Collection.from_dict(data)

    async def delete(self, collection_id: str) -> None:
        """Delete a collection.

        Args:
            collection_id: The UUID of the collection to delete.
        """
        await self._request("DELETE", f"/api/v1/collections/{collection_id}")
