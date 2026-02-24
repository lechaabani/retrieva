from core.connectors.rest_api import RestAPIConnector


class RestAPIConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = RestAPIConnector(
            base_url=cfg.get("base_url", ""),
            endpoints=cfg.get("endpoints"),
            auth_type=cfg.get("auth_type"),
            auth_token=cfg.get("auth_token"),
            auth_username=cfg.get("auth_username"),
            auth_password=cfg.get("auth_password"),
            api_key_header=cfg.get("api_key_header"),
            api_key_value=cfg.get("api_key_value"),
            api_key_query_param=cfg.get("api_key_query_param"),
            headers=cfg.get("headers"),
            max_pages=cfg.get("max_pages", 50),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
