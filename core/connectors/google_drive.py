"""Google Drive connector using OAuth2 and the Google Drive REST API v3."""

from __future__ import annotations

import io
import logging
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)

# MIME types that Google Workspace documents can be exported as plain text.
_EXPORT_MIME_MAP: dict[str, str] = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}

# Binary file extensions we can pass through the FileUploadConnector.
_DOWNLOADABLE_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".csv", ".html", ".htm"}


class GoogleDriveConnector(BaseConnector):
    """Connector for Google Drive using OAuth2 service-account or user credentials.

    Supports:
    * Listing files from a specific folder or the entire drive.
    * Downloading binary files (PDF, DOCX, etc.) and extracting text.
    * Exporting Google Workspace documents (Docs, Sheets, Slides) as text.
    * Incremental sync via ``last_sync_token`` (Drive changes API).
    """

    name = "google_drive"

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        service_account_json: Optional[str] = None,
        token: Optional[dict[str, str]] = None,
        folder_id: Optional[str] = None,
        include_shared: bool = False,
        file_types: Optional[list[str]] = None,
        max_files: int = 200,
        last_sync_token: Optional[str] = None,
    ) -> None:
        """
        Args:
            credentials_json: Path to an OAuth2 client-credentials JSON file.
            service_account_json: Path to a service-account JSON key file.
            token: Pre-existing OAuth2 token dict (access_token, refresh_token, etc.).
            folder_id: Google Drive folder ID to restrict listing.
            include_shared: Include files shared with the user.
            file_types: List of MIME type prefixes to include (e.g. ["application/pdf"]).
            max_files: Maximum number of files to retrieve.
            last_sync_token: Drive API changes start page token for incremental sync.
        """
        self.credentials_json = credentials_json
        self.service_account_json = service_account_json
        self.token = token
        self.folder_id = folder_id
        self.include_shared = include_shared
        self.file_types = file_types
        self.max_files = max_files
        self.last_sync_token = last_sync_token

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def _get_access_token(self) -> str:
        """Obtain a valid access token from the configured credentials."""
        import httpx

        # 1. Pre-existing token dict -----------------------------------------
        if self.token and self.token.get("access_token"):
            return self.token["access_token"]

        # 2. Service-account JSON (JWT exchange) ------------------------------
        if self.service_account_json:
            return await self._token_from_service_account()

        # 3. OAuth2 client credentials + refresh token ------------------------
        if self.credentials_json and self.token and self.token.get("refresh_token"):
            return await self._refresh_oauth_token()

        raise ConnectorError(
            "GoogleDriveConnector requires one of: token dict, "
            "service_account_json, or credentials_json + refresh_token."
        )

    async def _token_from_service_account(self) -> str:
        """Exchange a service-account JWT for an access token."""
        import json
        import time

        try:
            import jwt as pyjwt  # PyJWT
        except ImportError:
            raise ConnectorError("PyJWT is required for service-account auth: pip install PyJWT")

        with open(self.service_account_json, "r") as fh:
            sa = json.load(fh)

        now = int(time.time())
        payload = {
            "iss": sa["client_email"],
            "scope": "https://www.googleapis.com/auth/drive.readonly",
            "aud": sa["token_uri"],
            "iat": now,
            "exp": now + 3600,
        }
        signed = pyjwt.encode(payload, sa["private_key"], algorithm="RS256")

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                sa["token_uri"],
                data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": signed},
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def _refresh_oauth_token(self) -> str:
        """Refresh an OAuth2 user token."""
        import json

        with open(self.credentials_json, "r") as fh:
            creds = json.load(fh)

        installed = creds.get("installed") or creds.get("web") or creds
        client_id = installed["client_id"]
        client_secret = installed["client_secret"]

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": self.token["refresh_token"],
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self.token["access_token"] = data["access_token"]
            return data["access_token"]

    # ------------------------------------------------------------------
    # File listing
    # ------------------------------------------------------------------

    async def _list_files(self, client, headers: dict[str, str]) -> list[dict[str, Any]]:
        """List files using the Drive v3 files.list endpoint with pagination."""
        files: list[dict[str, Any]] = []
        page_token: Optional[str] = None

        query_parts: list[str] = ["trashed = false"]
        if self.folder_id:
            query_parts.append(f"'{self.folder_id}' in parents")
        q = " and ".join(query_parts)

        fields = "nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, size)"

        while len(files) < self.max_files:
            params: dict[str, Any] = {
                "q": q,
                "fields": fields,
                "pageSize": min(100, self.max_files - len(files)),
                "includeItemsFromAllDrives": str(self.include_shared).lower(),
                "supportsAllDrives": "true",
            }
            if page_token:
                params["pageToken"] = page_token

            resp = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            for f in data.get("files", []):
                if self.file_types:
                    if not any(f["mimeType"].startswith(ft) for ft in self.file_types):
                        continue
                files.append(f)
                if len(files) >= self.max_files:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return files

    # ------------------------------------------------------------------
    # File downloading / exporting
    # ------------------------------------------------------------------

    async def _download_file(self, client, headers: dict[str, str], file_meta: dict) -> Optional[Document]:
        """Download or export a single Drive file and return a Document."""
        file_id = file_meta["id"]
        mime = file_meta["mimeType"]
        name = file_meta["name"]

        try:
            # Google Workspace docs -> export as plain text
            if mime in _EXPORT_MIME_MAP:
                export_mime = _EXPORT_MIME_MAP[mime]
                resp = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                    headers=headers,
                    params={"mimeType": export_mime},
                )
                resp.raise_for_status()
                content = resp.text
                return Document(
                    content=content,
                    title=name,
                    source=file_meta.get("webViewLink", f"gdrive://{file_id}"),
                    metadata={
                        "connector": self.name,
                        "gdrive_id": file_id,
                        "mime_type": mime,
                        "modified_time": file_meta.get("modifiedTime", ""),
                    },
                )

            # Binary files -> download and extract via FileUploadConnector
            from pathlib import Path
            ext = Path(name).suffix.lower()
            if ext not in _DOWNLOADABLE_EXTENSIONS:
                logger.debug("Skipping unsupported file type: %s (%s)", name, mime)
                return None

            resp = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers=headers,
                params={"alt": "media"},
            )
            resp.raise_for_status()
            file_bytes = resp.content

            from core.connectors.file_upload import FileUploadConnector
            fu = FileUploadConnector(file_bytes=file_bytes, file_name=name)
            docs = await fu.pull()
            if docs:
                doc = docs[0]
                doc.source = file_meta.get("webViewLink", f"gdrive://{file_id}")
                doc.metadata.update({
                    "connector": self.name,
                    "gdrive_id": file_id,
                    "mime_type": mime,
                    "modified_time": file_meta.get("modifiedTime", ""),
                })
                return doc
            return None

        except Exception as exc:
            logger.warning("Failed to download/export %s (%s): %s", name, file_id, exc)
            return None

    # ------------------------------------------------------------------
    # Incremental sync
    # ------------------------------------------------------------------

    async def _list_changed_files(self, client, headers: dict[str, str]) -> list[dict[str, Any]]:
        """Use the Drive changes API for incremental sync."""
        if not self.last_sync_token:
            # Get initial start page token
            resp = await client.get(
                "https://www.googleapis.com/drive/v3/changes/startPageToken",
                headers=headers,
            )
            resp.raise_for_status()
            self.last_sync_token = resp.json()["startPageToken"]
            # First sync: fall back to full listing
            return await self._list_files(client, headers)

        files: list[dict[str, Any]] = []
        page_token = self.last_sync_token

        while page_token:
            resp = await client.get(
                "https://www.googleapis.com/drive/v3/changes",
                headers=headers,
                params={
                    "pageToken": page_token,
                    "fields": "nextPageToken, newStartPageToken, changes(fileId, file(id, name, mimeType, modifiedTime, webViewLink, size, trashed))",
                    "pageSize": 100,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            for change in data.get("changes", []):
                f = change.get("file")
                if f and not f.get("trashed", False):
                    files.append(f)

            page_token = data.get("nextPageToken")
            if not page_token:
                self.last_sync_token = data.get("newStartPageToken", self.last_sync_token)

        return files

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from Google Drive.

        Supports full listing or incremental sync via change tokens.

        Returns:
            List of Document instances extracted from Drive files.

        Raises:
            ConnectorError: On authentication or API errors.
        """
        import httpx

        try:
            access_token = await self._get_access_token()
            headers = self._build_headers(access_token)

            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                if self.last_sync_token:
                    file_list = await self._list_changed_files(client, headers)
                else:
                    file_list = await self._list_files(client, headers)

                logger.info("GoogleDrive: found %d files to process", len(file_list))

                documents: list[Document] = []
                for file_meta in file_list:
                    doc = await self._download_file(client, headers, file_meta)
                    if doc:
                        documents.append(doc)

                logger.info("GoogleDrive: extracted %d documents", len(documents))
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"Google Drive pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test connectivity by calling the Drive about endpoint.

        Returns:
            True if the API responds successfully.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            access_token = await self._get_access_token()
            headers = self._build_headers(access_token)

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://www.googleapis.com/drive/v3/about",
                    headers=headers,
                    params={"fields": "user"},
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            raise ConnectionTestFailedError(f"Google Drive connection test failed: {exc}") from exc
