# Connectors

Connectors allow Retrieva to pull documents from external data sources. This guide covers all built-in connectors, their configuration, and how to create custom ones.

## Overview

Connectors are defined in the `sources` section of `config.yaml`. Each connector syncs data from an external system into Retrieva collections.

```yaml
sources:
  - name: "My Source"
    connector: connector_type
    # connector-specific config...
```

## Built-in Connectors

### File Upload

Accepts direct file uploads through the API. This is the default connector and requires no external configuration.

**Type:** `file_upload`

| Option   | Type   | Required | Default            | Description                    |
|----------|--------|----------|--------------------|--------------------------------|
| `path`   | string | No       | `/data/documents/` | Local directory for file storage|

```yaml
sources:
  - name: "Documents"
    connector: file_upload
    path: /data/documents/
```

**Supported file types:** PDF, DOCX, XLSX, TXT, Markdown, CSV, HTML

**API usage:**

```bash
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "collection=my-docs"
```

**Limitations:**
- Maximum file size: configurable via `ingestion.max_file_size_mb` (default 100MB)
- Files are stored on the local filesystem or mounted volume

---

### Web Crawler

Crawls web pages and ingests their content.

**Type:** `web_crawler`

| Option            | Type     | Required | Default | Description                          |
|-------------------|----------|----------|---------|--------------------------------------|
| `url`             | string   | Yes      | --      | Starting URL to crawl                |
| `max_depth`       | int      | No       | `0`     | How many link levels to follow (0-3) |
| `allowed_domains` | list     | No       | `[]`    | Restrict crawling to these domains   |
| `exclude_patterns`| list     | No       | `[]`    | URL patterns to skip                 |
| `rate_limit`      | float    | No       | `1.0`   | Seconds between requests             |

```yaml
sources:
  - name: "Documentation Site"
    connector: web_crawler
    url: https://docs.example.com
    max_depth: 2
    allowed_domains:
      - docs.example.com
    exclude_patterns:
      - "/api/"
      - "/changelog/"
```

**API usage:**

```bash
curl -X POST http://localhost:8000/api/v1/ingest/url \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com/guide",
    "collection": "web-docs",
    "crawl_depth": 1
  }'
```

**Limitations:**
- JavaScript-rendered content is not supported (static HTML only)
- Respects `robots.txt` by default
- Maximum crawl depth is 3 levels

---

### Confluence

Syncs pages from Atlassian Confluence spaces.

**Type:** `confluence`

| Option       | Type   | Required | Default | Description                     |
|--------------|--------|----------|---------|---------------------------------|
| `url`        | string | Yes      | --      | Confluence base URL             |
| `space_key`  | string | Yes      | --      | Space key to sync               |
| `auth_token` | string | Yes      | --      | API token for authentication    |
| `username`   | string | No       | --      | Username (for basic auth)       |
| `page_limit` | int    | No       | `500`   | Maximum pages to sync           |
| `include_attachments` | bool | No | `false` | Also sync page attachments     |

```yaml
sources:
  - name: "Engineering Wiki"
    connector: confluence
    url: https://your-org.atlassian.net/wiki
    space_key: ENG
    auth_token: ${CONFLUENCE_TOKEN}
    include_attachments: true
```

**Limitations:**
- Requires a Confluence Cloud or Data Center API token
- Embedded images are not extracted (text only)
- Macro content may not render fully

---

### Amazon S3

Syncs documents from an S3 bucket.

**Type:** `s3`

| Option          | Type   | Required | Default | Description                     |
|-----------------|--------|----------|---------|---------------------------------|
| `bucket`        | string | Yes      | --      | S3 bucket name                  |
| `prefix`        | string | No       | `""`    | Key prefix to filter objects    |
| `region`        | string | No       | `us-east-1` | AWS region                 |
| `access_key_id` | string | No       | --      | AWS access key (or use IAM role)|
| `secret_access_key` | string | No  | --      | AWS secret key                  |

```yaml
sources:
  - name: "S3 Documents"
    connector: s3
    bucket: my-company-docs
    prefix: knowledge-base/
    region: us-west-2
```

**Limitations:**
- Only syncs files with supported extensions
- Large buckets may take time for initial sync

---

### Google Drive

Syncs documents from Google Drive folders.

**Type:** `google_drive`

| Option               | Type   | Required | Default | Description                    |
|----------------------|--------|----------|---------|--------------------------------|
| `folder_id`          | string | Yes      | --      | Google Drive folder ID         |
| `service_account_key`| string | Yes      | --      | Path to service account JSON   |
| `include_shared`     | bool   | No       | `false` | Include shared documents       |

```yaml
sources:
  - name: "Team Drive"
    connector: google_drive
    folder_id: "1A2B3C4D5E6F"
    service_account_key: /secrets/google-sa.json
```

**Limitations:**
- Requires a Google Cloud service account
- Google Docs are exported as plain text
- Sheets are exported as CSV

---

### Notion

Syncs pages from a Notion workspace.

**Type:** `notion`

| Option          | Type   | Required | Default | Description                    |
|-----------------|--------|----------|---------|--------------------------------|
| `api_key`       | string | Yes      | --      | Notion integration API key     |
| `database_id`   | string | No       | --      | Specific database to sync      |
| `page_ids`      | list   | No       | `[]`    | Specific pages to sync         |

```yaml
sources:
  - name: "Notion Knowledge Base"
    connector: notion
    api_key: ${NOTION_API_KEY}
    database_id: "abc123def456"
```

**Limitations:**
- Requires a Notion internal integration
- Nested databases are not recursively synced
- Rich media blocks (images, embeds) are skipped

## Creating a Custom Connector

Custom connectors implement the `BaseConnector` interface and can be placed in the `plugins/` directory.

### Connector Interface

```python
from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Base class for all data source connectors."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify the connection to the data source.

        Returns:
            True if the connection is successful.

        Raises:
            ConnectionTestFailedError: If the connection fails.
        """
        ...

    @abstractmethod
    async def fetch_documents(self) -> list[dict[str, Any]]:
        """Fetch documents from the data source.

        Returns:
            A list of dicts with 'content', 'title', and 'metadata' keys.
        """
        ...

    @abstractmethod
    async def fetch_document(self, document_id: str) -> dict[str, Any]:
        """Fetch a single document by its source ID.

        Returns:
            A dict with 'content', 'title', and 'metadata' keys.
        """
        ...
```

### Example: Custom RSS Connector

```python
# plugins/rss_connector.py
import httpx
from xml.etree import ElementTree

from core.connectors.base import BaseConnector


class RSSConnector(BaseConnector):
    """Connector that fetches articles from an RSS feed."""

    def __init__(self, config):
        super().__init__(config)
        self.feed_url = config["url"]

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.feed_url)
            return response.status_code == 200

    async def fetch_documents(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.feed_url)
            root = ElementTree.fromstring(response.text)

        documents = []
        for item in root.findall(".//item"):
            documents.append({
                "content": item.findtext("description", ""),
                "title": item.findtext("title", "Untitled"),
                "metadata": {
                    "source_url": item.findtext("link", ""),
                    "published": item.findtext("pubDate", ""),
                },
            })
        return documents

    async def fetch_document(self, document_id: str) -> dict:
        docs = await self.fetch_documents()
        for doc in docs:
            if doc["metadata"].get("source_url") == document_id:
                return doc
        raise ValueError(f"Document not found: {document_id}")
```

### Registering a Custom Connector

Place your connector file in the `plugins/` directory. Register it in `config.yaml`:

```yaml
sources:
  - name: "Tech Blog"
    connector: plugins.rss_connector.RSSConnector
    url: https://blog.example.com/feed.xml
```

## Sync Scheduling

Connectors can be configured for automatic periodic sync using the Celery beat scheduler. Configure sync intervals in your source definition:

```yaml
sources:
  - name: "Confluence"
    connector: confluence
    url: https://your-org.atlassian.net/wiki
    space_key: DOCS
    auth_token: ${CONFLUENCE_TOKEN}
    sync_interval: "0 */6 * * *"   # Every 6 hours (cron format)
```
