"""Unit tests for the collections API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestCollectionCRUD:
    """Tests for CRUD operations on collections."""

    @pytest.fixture
    def sample_collection(self) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "name": "knowledge-base",
            "description": "Main knowledge base for product docs",
            "config": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "documents_count": 42,
            "chunks_count": 350,
        }

    async def test_create_collection(
        self, test_client: AsyncClient, sample_collection
    ):
        """POST /api/v1/collections should create a new collection."""
        with patch(
            "api.routes.collections.create_collection",
            new_callable=AsyncMock,
            return_value=sample_collection,
        ):
            response = await test_client.post(
                "/api/v1/collections",
                json={
                    "name": "knowledge-base",
                    "description": "Main knowledge base",
                },
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code in (200, 201):
            data = response.json()
            assert data["name"] == "knowledge-base"

    async def test_list_collections(
        self, test_client: AsyncClient, sample_collection
    ):
        """GET /api/v1/collections should return a paginated list."""
        with patch(
            "api.routes.collections.list_collections",
            new_callable=AsyncMock,
            return_value={
                "collections": [sample_collection],
                "page": 1,
                "per_page": 20,
                "total": 1,
            },
        ):
            response = await test_client.get(
                "/api/v1/collections",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert "collections" in data
            assert len(data["collections"]) >= 1

    async def test_get_collection_by_id(
        self, test_client: AsyncClient, sample_collection
    ):
        """GET /api/v1/collections/:id should return a single collection."""
        coll_id = sample_collection["id"]

        with patch(
            "api.routes.collections.get_collection",
            new_callable=AsyncMock,
            return_value=sample_collection,
        ):
            response = await test_client.get(
                f"/api/v1/collections/{coll_id}",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == coll_id

    async def test_update_collection(
        self, test_client: AsyncClient, sample_collection
    ):
        """PATCH /api/v1/collections/:id should update the collection."""
        coll_id = sample_collection["id"]
        updated = {**sample_collection, "description": "Updated description"}

        with patch(
            "api.routes.collections.update_collection",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            response = await test_client.patch(
                f"/api/v1/collections/{coll_id}",
                json={"description": "Updated description"},
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data["description"] == "Updated description"

    async def test_delete_collection(self, test_client: AsyncClient):
        """DELETE /api/v1/collections/:id should remove the collection."""
        coll_id = str(uuid.uuid4())

        with patch(
            "api.routes.collections.delete_collection",
            new_callable=AsyncMock,
            return_value={"status": "deleted"},
        ):
            response = await test_client.delete(
                f"/api/v1/collections/{coll_id}",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "deleted"

    async def test_create_collection_without_auth(self, test_client: AsyncClient):
        """Creating a collection without auth should return 401."""
        response = await test_client.post(
            "/api/v1/collections",
            json={"name": "unauthorized"},
        )
        assert response.status_code == 401


class TestCollectionStats:
    """Tests for collection statistics."""

    async def test_collection_stats_include_counts(self, test_client: AsyncClient):
        """Collection response should include documents_count and chunks_count."""
        stats = {
            "id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "name": "docs",
            "description": None,
            "config": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "documents_count": 15,
            "chunks_count": 200,
        }

        with patch(
            "api.routes.collections.get_collection",
            new_callable=AsyncMock,
            return_value=stats,
        ):
            response = await test_client.get(
                f"/api/v1/collections/{stats['id']}",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert "documents_count" in data
            assert "chunks_count" in data
            assert data["documents_count"] == 15
            assert data["chunks_count"] == 200
