from core.connectors.confluence import ConfluenceConnector


class ConfluenceConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = ConfluenceConnector(
            base_url=cfg.get("url", ""),
            space_keys=[cfg["space_key"]] if cfg.get("space_key") else cfg.get("space_keys"),
            username=cfg.get("username"),
            api_token=cfg.get("api_token"),
            bearer_token=cfg.get("bearer_token"),
            max_pages=cfg.get("max_pages", 200),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
