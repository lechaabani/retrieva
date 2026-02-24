from core.connectors.slack import SlackConnector


class SlackConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = SlackConnector(
            bot_token=cfg.get("bot_token", ""),
            channel_ids=cfg.get("channel_ids"),
            channel_names=cfg.get("channel_names"),
            days_back=cfg.get("days_back", 30),
            include_threads=cfg.get("include_threads", True),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
