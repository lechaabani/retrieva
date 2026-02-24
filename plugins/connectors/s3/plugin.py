from core.connectors.s3 import S3Connector


class S3ConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = S3Connector(
            bucket=cfg.get("bucket", ""),
            prefix=cfg.get("prefix", ""),
            region_name=cfg.get("region", "us-east-1"),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
