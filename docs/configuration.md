# Configuration Reference

Retrieva is configured through a YAML file (`config.yaml`) with environment variable overrides. This document covers every configuration section in detail.

## Configuration Loading Order

1. **Defaults** -- Built-in defaults defined in `core/config.py`
2. **YAML file** -- Values from `config.yaml` override defaults
3. **Environment variables** -- Env vars override both defaults and YAML values

The YAML file path is resolved in this order:

- Explicit `CONFIG_PATH` environment variable
- `./config.yaml` relative to the project root

## Environment Variable Naming

Each configuration section uses a prefix. For example, the `ingestion` section uses the `INGESTION_` prefix. To override `default_chunk_size`, set:

```bash
export INGESTION_DEFAULT_CHUNK_SIZE=1024
```

Top-level platform settings use the `RETRIEVA_` prefix:

```bash
export RETRIEVA_ENVIRONMENT=production
export RETRIEVA_DEBUG=false
```

## Full Configuration Reference

### Platform Settings

Top-level settings for the application. Env prefix: `RETRIEVA_`.

```yaml
app_name: "Retrieva"        # Application display name
environment: "development"   # development | staging | production
debug: false                 # Enable debug mode (verbose logging, stack traces)
log_level: "INFO"            # DEBUG | INFO | WARNING | ERROR | CRITICAL
api_host: "0.0.0.0"         # API server bind address
api_port: 8000               # API server port
```

### Sources

Define data sources that feed documents into the ingestion pipeline. Sources are configured as a list under the `sources` key.

```yaml
sources:
  - name: "Documents"
    connector: file_upload
    path: /data/documents/

  - name: "Confluence"
    connector: confluence
    url: https://your-org.atlassian.net/wiki
    space_key: DOCS
    auth_token: ${CONFLUENCE_TOKEN}

  - name: "Website"
    connector: web_crawler
    url: https://docs.example.com
    max_depth: 3
    allowed_domains:
      - docs.example.com
```

### Ingestion Pipeline

Controls how documents are processed. Env prefix: `INGESTION_`.

| Key                          | Type     | Default                  | Description                                  |
|------------------------------|----------|--------------------------|----------------------------------------------|
| `default_chunking_strategy`  | string   | `semantic`               | Chunking strategy: `semantic`, `fixed`, `document` |
| `default_chunk_size`         | int      | `512`                    | Target tokens per chunk                      |
| `chunk_overlap`              | int      | `64`                     | Token overlap between consecutive chunks     |
| `default_embedding_model`    | string   | `text-embedding-3-small` | Embedding model name                         |
| `embedding_provider`         | string   | `openai`                 | Provider: `openai`, `sentence-transformers`, `cohere` |
| `embedding_dimensions`       | int      | `1536`                   | Vector dimensionality                        |
| `max_file_size_mb`           | int      | `100`                    | Maximum upload file size in MB               |
| `supported_extensions`       | list     | See below                | Allowed file extensions                      |
| `batch_size`                 | int      | `64`                     | Embedding batch size                         |

Default supported extensions: `.pdf`, `.docx`, `.xlsx`, `.txt`, `.md`, `.csv`, `.html`, `.htm`

```yaml
ingestion:
  chunking:
    strategy: semantic
    max_chunk_size: 512
    overlap: 50
  embedding:
    provider: openai
    model: text-embedding-3-small
```

### Retrieval Settings

Controls search and ranking behaviour. Env prefix: `RETRIEVAL_`.

| Key                    | Type   | Default                                    | Description                               |
|------------------------|--------|--------------------------------------------|-------------------------------------------|
| `default_strategy`     | string | `hybrid`                                   | Strategy: `vector`, `keyword`, `hybrid`   |
| `default_top_k`        | int    | `10`                                       | Number of chunks to retrieve              |
| `rerank_enabled`       | bool   | `true`                                     | Enable cross-encoder reranking            |
| `rerank_model`         | string | `cross-encoder/ms-marco-MiniLM-L-6-v2`    | Reranking model                           |
| `rerank_top_k`         | int    | `5`                                        | Chunks to keep after reranking            |
| `hybrid_vector_weight` | float  | `0.7`                                      | Vector score weight in hybrid mode        |
| `hybrid_keyword_weight`| float  | `0.3`                                      | Keyword score weight in hybrid mode       |
| `score_threshold`      | float  | `0.3`                                      | Minimum relevance score to include        |

```yaml
retrieval:
  strategy: hybrid
  vector_weight: 0.7
  top_k: 10
  reranking: true
  min_relevance_score: 0.5
```

### Generation Settings

Controls LLM answer generation. Env prefix: `GENERATION_`.

| Key                       | Type   | Default       | Description                              |
|---------------------------|--------|---------------|------------------------------------------|
| `default_provider`        | string | `openai`      | LLM provider: `openai`, `anthropic`      |
| `default_model`           | string | `gpt-4o`      | Model name                               |
| `temperature`             | float  | `0.1`         | Sampling temperature (0.0 = deterministic)|
| `max_tokens`              | int    | `2048`        | Maximum tokens in generated response     |
| `max_context_chunks`      | int    | `8`           | Maximum chunks to include in prompt      |
| `default_persona`         | string | See below     | System prompt / persona                  |
| `enable_guardrails`       | bool   | `true`        | Enable hallucination guardrails          |
| `hallucination_threshold` | float  | `0.5`         | Threshold for hallucination detection    |

```yaml
generation:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.1
  max_tokens: 1000
  persona: |
    You are a helpful AI assistant.
    Answer questions based only on the provided documents.
    Always cite your sources.
```

### Permissions and Access Control

Controls role-based access. Env prefix: `PERMISSIONS_`.

| Key             | Type   | Default             | Description                       |
|-----------------|--------|---------------------|-----------------------------------|
| `enabled`       | bool   | `true`              | Enable RBAC                       |
| `default_role`  | string | `viewer`            | Default role for new users        |
| `admin_roles`   | list   | `["admin", "owner"]`| Roles with administrative access  |

```yaml
permissions:
  enabled: true
  roles:
    admin:
      access: "*"
    viewer:
      access:
        - "Documents"
```

### Vector Database

Qdrant connection settings. Env prefix: `QDRANT_`.

| Key                 | Type   | Default      | Description                    |
|---------------------|--------|--------------|--------------------------------|
| `host`              | string | `localhost`  | Qdrant host                    |
| `port`              | int    | `6333`       | Qdrant HTTP port               |
| `grpc_port`         | int    | `6334`       | Qdrant gRPC port               |
| `api_key`           | string | `""`         | API key for Qdrant Cloud       |
| `prefer_grpc`       | bool   | `true`       | Use gRPC for better performance|
| `collection_prefix` | string | `retrieva_`  | Prefix for collection names    |

```yaml
vector_db:
  provider: qdrant
  url: http://qdrant:6333
```

### Relational Database

PostgreSQL connection settings. Env prefix: `DB_`.

| Key              | Type   | Default      | Description                     |
|------------------|--------|--------------|---------------------------------|
| `host`           | string | `localhost`  | Database host                   |
| `port`           | int    | `5432`       | Database port                   |
| `name`           | string | `retrieva`   | Database name                   |
| `user`           | string | `retrieva`   | Database user                   |
| `password`       | string | `""`         | Database password               |
| `pool_min_size`  | int    | `2`          | Minimum connection pool size    |
| `pool_max_size`  | int    | `10`         | Maximum connection pool size    |

The full DSN is also configurable via the `DATABASE_URL` environment variable.

### Redis

Redis connection settings. Env prefix: `REDIS_`.

| Key        | Type   | Default      | Description          |
|------------|--------|--------------|----------------------|
| `host`     | string | `localhost`  | Redis host           |
| `port`     | int    | `6379`       | Redis port           |
| `db`       | int    | `0`          | Redis database index |
| `password` | string | `""`         | Redis password       |

### Analytics

Usage tracking and telemetry. Env prefix: `ANALYTICS_`.

| Key               | Type | Default | Description                       |
|-------------------|------|---------|-----------------------------------|
| `enabled`         | bool | `true`  | Enable analytics tracking         |
| `track_queries`   | bool | `true`  | Log query content                 |
| `track_latency`   | bool | `true`  | Track response latency            |
| `retention_days`  | int  | `90`    | Days to retain analytics data     |

## Common Configuration Examples

### Minimal local development

```yaml
generation:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.1

ingestion:
  chunking:
    strategy: fixed
    max_chunk_size: 256
```

### Production with Anthropic

```yaml
generation:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.1
  max_tokens: 2000

ingestion:
  embedding:
    provider: openai
    model: text-embedding-3-large

retrieval:
  strategy: hybrid
  reranking: true
  min_relevance_score: 0.5

permissions:
  enabled: true
```

### Local embeddings (no API calls for embedding)

```yaml
ingestion:
  embedding:
    provider: sentence-transformers
    model: all-MiniLM-L6-v2
    device: cpu
```
