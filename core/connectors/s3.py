"""AWS S3 connector for listing and downloading objects."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError

logger = logging.getLogger(__name__)


class S3Connector(BaseConnector):
    """Connector for listing and downloading files from an S3 bucket.

    Uses boto3 for AWS API calls and delegates content extraction to
    the file upload connector.
    """

    name = "s3"

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        suffix_filter: Optional[list[str]] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        max_files: int = 100,
    ) -> None:
        """
        Args:
            bucket: S3 bucket name.
            prefix: Object key prefix to filter by.
            suffix_filter: List of file extensions to include (e.g. [".pdf", ".docx"]).
            aws_access_key_id: AWS access key. Falls back to env / IAM role.
            aws_secret_access_key: AWS secret key.
            region_name: AWS region.
            max_files: Maximum number of files to download.
        """
        self.bucket = bucket
        self.prefix = prefix
        self.suffix_filter = [s.lower() for s in (suffix_filter or [])]
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.max_files = max_files

    def _get_client(self):
        """Create a boto3 S3 client."""
        try:
            import boto3
        except ImportError:
            raise ConnectorError("boto3 is required for S3Connector: pip install boto3")

        kwargs = {"region_name": self.region_name}
        if self.aws_access_key_id:
            kwargs["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            kwargs["aws_secret_access_key"] = self.aws_secret_access_key

        return boto3.client("s3", **kwargs)

    async def pull(self) -> list[Document]:
        """List and download files from the configured S3 bucket.

        Returns:
            List of Documents extracted from downloaded files.

        Raises:
            ConnectorError: On AWS or extraction errors.
        """
        import asyncio

        from core.connectors.file_upload import FileUploadConnector

        try:
            client = self._get_client()

            # List objects
            paginator = client.get_paginator("list_objects_v2")
            keys: list[str] = []

            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if self.suffix_filter:
                        if not any(key.lower().endswith(s) for s in self.suffix_filter):
                            continue
                    keys.append(key)
                    if len(keys) >= self.max_files:
                        break
                if len(keys) >= self.max_files:
                    break

            logger.info("Found %d files in s3://%s/%s", len(keys), self.bucket, self.prefix)

            # Download and extract each file
            documents: list[Document] = []
            for key in keys:
                try:
                    response = client.get_object(Bucket=self.bucket, Key=key)
                    file_bytes = response["Body"].read()
                    file_name = Path(key).name

                    connector = FileUploadConnector(file_bytes=file_bytes, file_name=file_name)
                    docs = await connector.pull()
                    for doc in docs:
                        doc.source = f"s3://{self.bucket}/{key}"
                        doc.metadata["s3_key"] = key
                        doc.metadata["s3_bucket"] = self.bucket
                    documents.extend(docs)

                except Exception as exc:
                    logger.warning("Failed to process s3://%s/%s: %s", self.bucket, key, exc)
                    continue

            return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"S3 pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False
