from core.connectors.google_drive import GoogleDriveConnector


class GoogleDriveConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = GoogleDriveConnector(
            service_account_json=cfg.get("service_account_json"),
            credentials_json=cfg.get("credentials_json"),
            token=cfg.get("token"),
            folder_id=cfg.get("folder_id"),
            include_shared=cfg.get("include_shared", False),
            max_files=cfg.get("max_files", 200),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
