from core.connectors.file_upload import FileUploadConnector


class FileUploadConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = FileUploadConnector(
            upload_dir=cfg.get("upload_dir", "/data/documents"),
        )

    def connect(self):
        return self._impl.connect()

    def fetch(self):
        return self._impl.fetch()
