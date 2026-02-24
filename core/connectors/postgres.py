"""PostgreSQL connector for querying database tables and views."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)


class PostgresConnector(BaseConnector):
    """Connector for PostgreSQL databases using asyncpg.

    Supports:
    * Connecting with a DSN or individual connection parameters.
    * Pulling rows from specified tables/views as documents.
    * Executing custom SQL queries.
    * Configurable content and title column mapping.
    * Row-level or table-level document grouping.
    """

    name = "postgres"

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: Optional[str] = None,
        tables: Optional[list[str]] = None,
        query: Optional[str] = None,
        content_columns: Optional[list[str]] = None,
        title_column: Optional[str] = None,
        max_rows: int = 1000,
        group_by_table: bool = False,
        ssl: bool = False,
    ) -> None:
        """
        Args:
            dsn: Full PostgreSQL connection string (postgresql://user:pass@host:port/db).
            host: Database host.
            port: Database port.
            database: Database name.
            user: Database user.
            password: Database password.
            tables: List of table or view names to pull from.
            query: Custom SQL query to execute instead of table listing.
            content_columns: Column names whose values form the document content.
                If None, all columns are concatenated.
            title_column: Column name to use as the document title.
            max_rows: Maximum rows to retrieve per table/query.
            group_by_table: If True, combine all rows of a table into one Document.
            ssl: Whether to use SSL for the connection.
        """
        self.dsn = dsn
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.tables = tables or []
        self.query = query
        self.content_columns = content_columns
        self.title_column = title_column
        self.max_rows = max_rows
        self.group_by_table = group_by_table
        self.ssl = ssl

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_connection(self):
        """Create an asyncpg connection."""
        try:
            import asyncpg
        except ImportError:
            raise ConnectorError("asyncpg is required for PostgresConnector: pip install asyncpg")

        try:
            if self.dsn:
                conn = await asyncpg.connect(self.dsn, ssl=self.ssl if self.ssl else None)
            else:
                conn = await asyncpg.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    ssl=self.ssl if self.ssl else None,
                )
            return conn
        except Exception as exc:
            raise ConnectorError(f"PostgreSQL connection failed: {exc}") from exc

    def _row_to_content(self, row: dict[str, Any], columns: list[str]) -> str:
        """Convert a database row to text content."""
        if self.content_columns:
            parts = []
            for col in self.content_columns:
                val = row.get(col)
                if val is not None:
                    parts.append(str(val))
            return "\n".join(parts)

        # Use all columns
        parts = []
        for col in columns:
            val = row.get(col)
            if val is not None:
                parts.append(f"{col}: {val}")
        return "\n".join(parts)

    def _row_title(self, row: dict[str, Any], table_name: str, idx: int) -> str:
        """Extract a title for a row-level document."""
        if self.title_column and self.title_column in row:
            return str(row[self.title_column])
        return f"{table_name} row {idx + 1}"

    async def _fetch_table(self, conn, table_name: str) -> list[Document]:
        """Fetch rows from a single table and convert to Documents."""
        # Sanitize table name: allow only alphanumeric, underscore, dot, and dash
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.\-]*$', table_name):
            logger.warning("Skipping table with invalid name: %s", table_name)
            return []

        query = f'SELECT * FROM "{table_name}" LIMIT {self.max_rows}'
        rows = await conn.fetch(query)

        if not rows:
            return []

        columns = list(rows[0].keys())
        documents: list[Document] = []

        if self.group_by_table:
            # Combine all rows into a single document
            parts: list[str] = []
            for row in rows:
                row_dict = dict(row)
                parts.append(self._row_to_content(row_dict, columns))
            content = "\n\n---\n\n".join(parts)
            documents.append(Document(
                content=content,
                title=f"Table: {table_name}",
                source=f"postgres://{self.host}:{self.port}/{self.database}/{table_name}",
                metadata={
                    "connector": self.name,
                    "database": self.database,
                    "table": table_name,
                    "row_count": len(rows),
                },
            ))
        else:
            # Each row becomes its own document
            for idx, row in enumerate(rows):
                row_dict = dict(row)
                content = self._row_to_content(row_dict, columns)
                if not content.strip():
                    continue
                title = self._row_title(row_dict, table_name, idx)
                documents.append(Document(
                    content=content,
                    title=title,
                    source=f"postgres://{self.host}:{self.port}/{self.database}/{table_name}#{idx}",
                    metadata={
                        "connector": self.name,
                        "database": self.database,
                        "table": table_name,
                        "row_index": idx,
                    },
                ))

        return documents

    async def _execute_query(self, conn, query: str) -> list[Document]:
        """Execute a custom SQL query and convert results to Documents."""
        rows = await conn.fetch(query)

        if not rows:
            return []

        columns = list(rows[0].keys())
        documents: list[Document] = []

        if self.group_by_table:
            parts: list[str] = []
            for row in rows:
                row_dict = dict(row)
                parts.append(self._row_to_content(row_dict, columns))
            content = "\n\n---\n\n".join(parts)
            documents.append(Document(
                content=content,
                title="Custom Query Results",
                source=f"postgres://{self.host}:{self.port}/{self.database}/query",
                metadata={
                    "connector": self.name,
                    "database": self.database,
                    "query": query[:200],
                    "row_count": len(rows),
                },
            ))
        else:
            for idx, row in enumerate(rows):
                row_dict = dict(row)
                content = self._row_to_content(row_dict, columns)
                if not content.strip():
                    continue
                title = self._row_title(row_dict, "query", idx)
                documents.append(Document(
                    content=content,
                    title=title,
                    source=f"postgres://{self.host}:{self.port}/{self.database}/query#{idx}",
                    metadata={
                        "connector": self.name,
                        "database": self.database,
                        "row_index": idx,
                    },
                ))

        return documents

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from PostgreSQL tables or a custom query.

        Returns:
            List of Document instances from database rows.

        Raises:
            ConnectorError: On connection or query errors.
        """
        try:
            conn = await self._get_connection()

            try:
                documents: list[Document] = []

                if self.query:
                    docs = await self._execute_query(conn, self.query)
                    documents.extend(docs)
                    logger.info("PostgreSQL: fetched %d docs from custom query", len(docs))
                elif self.tables:
                    for table in self.tables:
                        docs = await self._fetch_table(conn, table)
                        documents.extend(docs)
                        logger.info("PostgreSQL: fetched %d docs from table %s", len(docs), table)
                else:
                    # Auto-discover tables in public schema
                    rows = await conn.fetch(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                        "ORDER BY tablename LIMIT 50"
                    )
                    for row in rows:
                        table = row["tablename"]
                        docs = await self._fetch_table(conn, table)
                        documents.extend(docs)

                logger.info("PostgreSQL: total %d documents", len(documents))
                return documents

            finally:
                await conn.close()

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"PostgreSQL pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test connectivity by executing a simple query.

        Returns:
            True if the database responds.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        try:
            conn = await self._get_connection()
            try:
                await conn.fetchval("SELECT 1")
                return True
            finally:
                await conn.close()
        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectionTestFailedError(f"PostgreSQL connection test failed: {exc}") from exc
