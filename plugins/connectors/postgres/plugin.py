from core.connectors.postgres import PostgresConnector


class PostgresConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = PostgresConnector(
            dsn=cfg.get("dsn"),
            host=cfg.get("host", "localhost"),
            port=cfg.get("port", 5432),
            database=cfg.get("database", "postgres"),
            user=cfg.get("user", "postgres"),
            password=cfg.get("password"),
            tables=cfg.get("tables"),
            query=cfg.get("query"),
            content_columns=cfg.get("content_columns"),
            title_column=cfg.get("title_column"),
            max_rows=cfg.get("max_rows", 1000),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
