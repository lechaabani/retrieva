"""Data source connectors for ingesting content from external systems."""

from core.connectors.base import BaseConnector, Document
from core.connectors.confluence import ConfluenceConnector
from core.connectors.file_upload import FileUploadConnector
from core.connectors.github_connector import GitHubConnector
from core.connectors.google_drive import GoogleDriveConnector
from core.connectors.notion import NotionConnector
from core.connectors.postgres import PostgresConnector
from core.connectors.rest_api import RestAPIConnector
from core.connectors.s3 import S3Connector
from core.connectors.slack import SlackConnector
from core.connectors.url_crawler import URLCrawlerConnector

_CONNECTOR_MAP: dict[str, type[BaseConnector]] = {
    "confluence": ConfluenceConnector,
    "file_upload": FileUploadConnector,
    "github": GitHubConnector,
    "google_drive": GoogleDriveConnector,
    "notion": NotionConnector,
    "postgres": PostgresConnector,
    "rest_api": RestAPIConnector,
    "s3": S3Connector,
    "slack": SlackConnector,
    "url_crawler": URLCrawlerConnector,
}


def get_connector(source_type: str, config: dict | None = None) -> BaseConnector:
    """Instantiate a connector by type name.

    Tries the plugin manager first, then falls back to built-in connectors.

    Args:
        source_type: Connector type key (e.g. "s3", "confluence", "github").
        config: Connector-specific configuration dict.

    Returns:
        An initialised BaseConnector instance.

    Raises:
        ValueError: If the connector type is unknown.
    """
    # Try plugin manager first
    try:
        from core.plugin_system.manager import get_plugin_manager

        pm = get_plugin_manager()
        return pm.get_plugin("connector", source_type)
    except Exception:
        pass

    # Fallback to built-in
    cls = _CONNECTOR_MAP.get(source_type)
    if cls is None:
        raise ValueError(
            f"Unknown connector type: '{source_type}'. "
            f"Available: {', '.join(sorted(_CONNECTOR_MAP))}"
        )
    return cls(**(config or {}))


__all__ = [
    "BaseConnector",
    "Document",
    "get_connector",
    "ConfluenceConnector",
    "FileUploadConnector",
    "GitHubConnector",
    "GoogleDriveConnector",
    "NotionConnector",
    "PostgresConnector",
    "RestAPIConnector",
    "S3Connector",
    "SlackConnector",
    "URLCrawlerConnector",
]
