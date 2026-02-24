# Retrieva Python SDK

Official Python client for the [Retrieva](https://retrieva.io) RAG (Retrieval-Augmented Generation) platform.

## Installation

```bash
pip install retrieva
```

## Quick Start

```python
from retrieva import Retrieva

rag = Retrieva(api_key="rtv_xxx", base_url="https://api.example.com")

# Ask a question with RAG
result = rag.query("How do I configure authentication?", collection_id="my-collection")
print(result.answer)
print(result.confidence)
for source in result.sources:
    print(f"  - {source.title} (score: {source.score})")
```

## Authentication

All API requests require a Bearer token. Pass your API key when creating a client:

```python
rag = Retrieva(api_key="rtv_your_key_here")
```

## Usage

### RAG Query

Perform a retrieval-augmented generation query to get an AI-generated answer grounded in your documents:

```python
result = rag.query(
    "What are the system requirements?",
    collection_id="docs-collection-uuid",
    top_k=5,
    include_sources=True,
    language="en",
)

print(result.answer)       # The generated answer
print(result.confidence)   # Confidence score (0-1)
print(result.sources)      # List of Source objects
```

### Semantic Search

Search your documents using semantic similarity:

```python
hits = rag.search("deployment configuration", collection_id="docs", top_k=10)

for hit in hits.results:
    print(f"{hit.title}: {hit.score:.3f}")
    print(f"  {hit.content[:200]}")
```

### Document Ingestion

#### Upload a File

```python
response = rag.ingest.file(
    "path/to/document.pdf",
    collection="my-collection",
    metadata={"department": "engineering"},
)
print(f"Document ingested: {response.document_id}")
```

#### Ingest Text

```python
response = rag.ingest.text(
    "This is the content of my document...",
    title="My Document",
    collection="my-collection",
)
```

#### Ingest from URL

```python
response = rag.ingest.url(
    "https://docs.example.com/guide",
    collection="my-collection",
    crawl_depth=2,
)
```

### Collections

```python
# List all collections
collections = rag.collections.list()
for col in collections:
    print(f"{col.name} ({col.document_count} docs)")

# Create a collection
new_col = rag.collections.create(
    name="engineering-docs",
    description="Internal engineering documentation",
)

# Get a collection
col = rag.collections.get("collection-uuid")

# Update a collection
updated = rag.collections.update("collection-uuid", name="new-name")

# Delete a collection
rag.collections.delete("collection-uuid")
```

### Widget Client

For public-facing widget integrations that use a separate widget API key:

```python
from retrieva import Widget

widget = Widget(api_key="rtv_pub_xxx", widget_id="widget-uuid")

# Query
answer = widget.query("How does pricing work?")
print(answer.answer)

# Search
results = widget.search("pricing plans", top_k=5)
for hit in results.results:
    print(hit.title, hit.score)
```

## Async Support

Every client has an async counterpart:

```python
import asyncio
from retrieva import AsyncRetrieva, AsyncWidget

async def main():
    async with AsyncRetrieva(api_key="rtv_xxx") as rag:
        result = await rag.query("How to deploy?")
        print(result.answer)

        hits = await rag.search("deployment")
        print(f"Found {hits.total} results")

        response = await rag.ingest.text(
            "New content", title="Doc", collection="docs"
        )
        print(response.document_id)

    async with AsyncWidget(api_key="rtv_pub_xxx", widget_id="uuid") as widget:
        answer = await widget.query("Question?")
        print(answer.answer)

asyncio.run(main())
```

## Error Handling

The SDK raises typed exceptions for different error conditions:

```python
from retrieva import Retrieva, AuthenticationError, NotFoundError, RateLimitError

rag = Retrieva(api_key="rtv_xxx")

try:
    result = rag.query("question")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Collection not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except RetrievaError as e:
    print(f"API error {e.status_code}: {e.message}")
```

### Exception Hierarchy

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `RetrievaError` | -- | Base exception for all SDK errors |
| `AuthenticationError` | 401, 403 | Invalid or missing API key |
| `NotFoundError` | 404 | Resource not found |
| `ValidationError` | 422 | Request validation failed |
| `RateLimitError` | 429 | Rate limit exceeded |
| `ServerError` | 5xx | Server-side error |
| `ConnectionError` | -- | Cannot connect to the API |
| `TimeoutError` | -- | Request timed out |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | (required) | Your Retrieva API key |
| `base_url` | `https://api.retrieva.io` | API base URL |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `2` | Retries on transient failures |

## Context Manager

Both sync and async clients support context managers for automatic cleanup:

```python
with Retrieva(api_key="rtv_xxx") as rag:
    result = rag.query("question")
# Client is automatically closed
```

## Response Types

All API responses are returned as typed dataclasses:

- `QueryResult` -- answer, sources, confidence, query, collection_id, metadata
- `SearchResult` -- results (list of SearchHit), query, total, metadata
- `SearchHit` -- content, title, source, score, document_id, collection_id, metadata
- `Source` -- content, title, source, score, metadata
- `Collection` -- id, name, description, document_count, created_at, updated_at, metadata
- `Document` -- id, title, content, source, collection_id, status, created_at, updated_at, metadata
- `IngestResponse` -- document_id, status, message, collection_id, metadata
- `WidgetQueryResult` -- answer, sources, confidence, metadata
- `WidgetSearchResult` -- results, query, total, metadata

## License

MIT
