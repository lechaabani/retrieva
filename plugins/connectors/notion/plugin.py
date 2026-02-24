from core.connectors.notion import NotionConnector


class NotionConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = NotionConnector(
            api_key=cfg.get("api_key", ""),
            database_ids=cfg.get("database_ids"),
            page_ids=cfg.get("page_ids"),
            max_pages=cfg.get("max_pages", 200),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
