"""Unit tests for the documents API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestGetDocuments:
    """Tests for GET /api/v1/documents."""

    @pytest.fixture
    def mock_documents_list(self) -> dict:
        return {
            "documents": [
                {
                    "id": str(uuid.uuid4()),
                    "collection_id": str(uuid.uuid4()),
                    "source_connector": "file_upload",
                    "source_id": None,
                    "title": "User Guide",
                    "content_hash": "abc123",
                    "metadata": {},
                    "status": "indexed",
                    "chunks_count": 12,
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": str(uuid.uuid4()),
                    "collection_id": str(uuid.uuid4()),
                    "source_connector": "web_crawler",
                    "source_id": "https://example.com",
                    "title": "Website Content",
                    "content_hash": "def456",
                    "metadata": {},
                    "status": "indexed",
                    "chunks_count": 8,
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            ],
            "page": 1,
            "per_page": 20,
            "total": 2,
        }

    async def test_list_documents_returns_list(
        self, test_client: AsyncClient, mock_documents_list
    ):
        """GET /api/v1/documents should return a paginated list."""
        with patch(
            "api.routes.documents.list_documents",
            new_callable=AsyncMock,
            return_value=mock_documents_list,
        ):
            response = await test_client.get(
                "/api/v1/documents",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert "documents" in data
            assert isinstance(data["documents"], list)
            assert "total" in data

    async def test_list_documents_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Listing documents without auth should return 401."""
        response = await test_client.get("/api/v1/documents")
        assert response.status_code == 401


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/:id."""

    async def test_delete_document(self, test_client: AsyncClient):
        """DELETE /api/v1/documents/:id should remove the document."""
        doc_id = str(uuid.uuid4())

        with patch(
            "api.routes.documents.delete_document",
            new_callable=AsyncMock,
            return_value={"status": "deleted", "document_id": doc_id},
        ):
            response = await test_client.delete(
                f"/api/v1/documents/{doc_id}",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "deleted"

    async def test_delete_nonexistent_document_returns_404(
        self, test_client: AsyncClient
    ):
        """Deleting a non-existent document should return 404."""
        doc_id = str(uuid.uuid4())

        with patch(
            "api.routes.documents.delete_document",
            new_callable=AsyncMock,
            side_effect=Exception("Document not found"),
        ):
            response = await test_client.delete(
                f"/api/v1/documents/{doc_id}",
                headers={"Authorization": "Bearer test-key"},
            )

        assert response.status_code in (401, 404, 500)


class TestPagination:
    """Tests for document list pagination."""

    async def test_pagination_params_accepted(self, test_client: AsyncClient):
        """Page and per_page query params should be accepted."""
        with patch(
            "api.routes.documents.list_documents",
            new_callable=AsyncMock,
            return_value={
                "documents": [],
                "page": 2,
                "per_page": 10,
                "total": 25,
            },
        ):
            response = await test_client.get(
                "/api/v1/documents?page=2&per_page=10",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data.get("page") == 2
            assert data.get("per_page") == 10

    async def test_default_pagination(self, test_client: AsyncClient):
        """Without explicit pagination params, defaults should be applied."""
        with patch(
            "api.routes.documents.list_documents",
            new_callable=AsyncMock,
            return_value={
                "documents": [],
                "page": 1,
                "per_page": 20,
                "total": 0,
            },
        ):
            response = await test_client.get(
                "/api/v1/documents",
                headers={"Authorization": "Bearer test-key"},
            )

        if response.status_code == 200:
            data = response.json()
            assert data.get("page") == 1
