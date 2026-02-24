"""PostgreSQL connector for pulling documents from database queries."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError

logger = logging.getLogger(__name__)


class PostgresConnector(BaseConnector):
    """Connector that executes a SQL query and maps rows to Documents.

    Each row is converted into a Document using configurable column mappings.
    """

    name = "postgres"

    def __init__(
        self,
        dsn: str,
        query: str,
        content_column: str = "content",
        title_column: str = "title",
        source_column: Optional[str] = None,
        metadata_columns: Optional[list[str]] = None,
    ) -> None:
        """
        Args:
            dsn: PostgreSQL connection string.
            query: SQL query to execute. Should be a SELECT statement.
            content_column: Column name containing document text.
            title_column: Column name for document title.
            source_column: Column name for document source identifier.
            metadata_columns: Additional columns to include in metadata.
        """
        self.dsn = dsn
        self.query = query
        self.content_column = content_column
        self.title_column = title_column
        self.source_column = source_column
        self.metadata_columns = metadata_columns or []

    async def pull(self) -> list[Document]:
        """Execute the configured query and map rows to Documents.

        Returns:
            List of Documents, one per result row.

        Raises:
            ConnectorError: On database errors.
        """
        try:
            import asyncpg
        except ImportError:
            raise ConnectorError("asyncpg is required for PostgresConnector: pip install asyncpg")

        try:
            conn = await asyncpg.connect(self.dsn)
            try:
                rows = await conn.fetch(self.query)
            finally:
                await conn.close()

            documents: list[Document] = []
            for row in rows:
                row_dict = dict(row)

                content = str(row_dict.get(self.content_column, ""))
                if not content.strip():
                    continue

                title = str(row_dict.get(self.title_column, "Untitled"))
                source = str(row_dict.get(self.source_column, "postgres")) if self.source_column else "postgres"

                metadata: dict[str, Any] = {"connector": self.name, "source_type": "database"}
                for col in self.metadata_columns:
                    if col in row_dict:
                        val = row_dict[col]
                        # Convert non-serializable types to string
                        metadata[col] = str(val) if not isinstance(val, (str, int, float, bool, type(None))) else val

                documents.append(
                    Document(
                        content=content,
                        title=title,
                        source=source,
                        metadata=metadata,
                    )
                )

            logger.info("PostgresConnector fetched %d documents", len(documents))
            return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"PostgreSQL query failed: {exc}") from exc

    async def test_connection(self) -> bool:
        try:
            import asyncpg

            conn = await asyncpg.connect(self.dsn)
            await conn.execute("SELECT 1")
            await conn.close()
            return True
        except Exception:
            return False
