# API Reference

Complete reference for the Retrieva REST API. All endpoints are prefixed with `/api/v1`.

## Authentication

Retrieva supports two authentication methods:

### API Keys

Include your API key in the `Authorization` header:

```
Authorization: Bearer rtv_your_api_key_here
```

API keys are generated through the admin interface or the `/api/v1/auth/keys` endpoint. Keys are prefixed with `rtv_` and can be scoped with permissions.

### JWT Tokens

For user-based authentication, obtain a JWT token via login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Tokens expire after 60 minutes by default (configurable via `JWT_EXPIRE_MINUTES`).

## Rate Limiting

API requests are rate-limited per API key. Default limits:

| Endpoint Category | Limit            |
|-------------------|------------------|
| Query / Search    | 60 requests/min  |
| Ingestion         | 30 requests/min  |
| Admin             | 20 requests/min  |
| Other             | 120 requests/min |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1706140800
```

## Error Codes

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning                                       |
|-------------|-----------------------------------------------|
| 400         | Bad Request -- Invalid parameters or payload  |
| 401         | Unauthorized -- Missing or invalid credentials|
| 403         | Forbidden -- Insufficient permissions         |
| 404         | Not Found -- Resource does not exist          |
| 409         | Conflict -- Resource already exists           |
| 413         | Payload Too Large -- File exceeds size limit  |
| 422         | Unprocessable Entity -- Validation error      |
| 429         | Too Many Requests -- Rate limit exceeded      |
| 500         | Internal Server Error                         |

## Pagination

List endpoints support pagination via query parameters:

| Parameter  | Type | Default | Range   | Description                |
|------------|------|---------|---------|----------------------------|
| `page`     | int  | `1`     | >= 1    | Page number                |
| `per_page` | int  | `20`    | 1 - 100 | Items per page            |

Paginated responses include:

```json
{
  "items": [...],
  "page": 1,
  "per_page": 20,
  "total": 156
}
```

---

## Endpoints

### Query

#### POST /api/v1/query

Perform a full RAG query: retrieves relevant chunks and generates an answer.

**Request Body:**

| Field        | Type   | Required | Description                       |
|--------------|--------|----------|-----------------------------------|
| `question`   | string | Yes      | The question to answer (1-2000 chars) |
| `collection` | string | Yes      | Target collection name            |
| `options`    | object | No       | Query tuning options              |

**Options object:**

| Field             | Type | Default | Description                     |
|-------------------|------|---------|---------------------------------|
| `top_k`           | int  | `10`    | Number of chunks to retrieve    |
| `include_sources`  | bool | `true`  | Include source references       |
| `language`        | string | `en`  | Response language code          |
| `max_tokens`      | int  | `500`   | Maximum tokens in answer        |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is our refund policy?",
    "collection": "knowledge-base",
    "options": {
      "top_k": 5,
      "include_sources": true
    }
  }'
```

**Response (200):**

```json
{
  "answer": "According to the company policy, refunds are available within 30 days of purchase.",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "title": "Refund Policy",
      "content": "Customers may request a refund within 30 days...",
      "score": 0.94,
      "metadata": {}
    }
  ],
  "confidence": 0.94,
  "tokens_used": 150
}
```

---

#### POST /api/v1/search

Perform a semantic search without answer generation. Returns matching chunks.

**Request Body:**

| Field        | Type   | Required | Description                       |
|--------------|--------|----------|-----------------------------------|
| `query`      | string | Yes      | Search query (1-2000 chars)       |
| `collection` | string | Yes      | Target collection name            |
| `top_k`      | int    | No       | Number of results (default 10)    |
| `filters`    | object | No       | Metadata filters                  |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "refund policy",
    "collection": "knowledge-base",
    "top_k": 5,
    "filters": {"source_type": "pdf"}
  }'
```

**Response (200):**

```json
{
  "results": [
    {
      "chunk_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Refund Policy",
      "content": "Customers may request a refund within 30 days...",
      "score": 0.94,
      "metadata": {"source_type": "pdf"}
    }
  ],
  "total": 1
}
```

---

### Ingestion

#### POST /api/v1/ingest/text

Ingest raw text content.

**Request Body:**

| Field        | Type   | Required | Description                       |
|--------------|--------|----------|-----------------------------------|
| `content`    | string | Yes      | Text content to ingest            |
| `title`      | string | Yes      | Document title                    |
| `collection` | string | Yes      | Target collection name            |
| `metadata`   | object | No       | Arbitrary metadata                |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your document text here...",
    "title": "My Document",
    "collection": "my-docs"
  }'
```

**Response (200):**

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "chunks_count": 0,
  "message": "Document accepted for processing."
}
```

---

#### POST /api/v1/ingest/file

Upload and ingest a file.

**Request:** `multipart/form-data`

| Field        | Type   | Required | Description                       |
|--------------|--------|----------|-----------------------------------|
| `file`       | file   | Yes      | The file to upload                |
| `collection` | string | Yes      | Target collection name            |
| `metadata`   | string | No       | JSON string of metadata           |

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "collection=my-docs"
```

---

#### POST /api/v1/ingest/url

Ingest content from a URL.

**Request Body:**

| Field         | Type   | Required | Description                       |
|---------------|--------|----------|-----------------------------------|
| `url`         | string | Yes      | URL to crawl and ingest           |
| `collection`  | string | Yes      | Target collection name            |
| `crawl_depth` | int    | No       | Link levels to follow (0-3)       |
| `metadata`    | object | No       | Arbitrary metadata                |

---

### Documents

#### GET /api/v1/documents

List documents with pagination.

**Query Parameters:** `page`, `per_page`, `collection`, `status`

**Response (200):**

```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "collection_id": "...",
      "source_connector": "file_upload",
      "title": "User Guide",
      "status": "indexed",
      "chunks_count": 12,
      "indexed_at": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-15T10:28:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 42
}
```

---

#### GET /api/v1/documents/{id}

Get a single document by ID.

---

#### DELETE /api/v1/documents/{id}

Delete a document and its associated chunks and vectors.

**Response (200):**

```json
{
  "status": "deleted",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### Collections

#### POST /api/v1/collections

Create a new collection.

**Request Body:**

| Field         | Type   | Required | Description                       |
|---------------|--------|----------|-----------------------------------|
| `name`        | string | Yes      | Collection name (1-255 chars)     |
| `description` | string | No       | Human-readable description        |
| `config`      | object | No       | Collection-level config overrides  |

---

#### GET /api/v1/collections

List all collections with pagination.

---

#### GET /api/v1/collections/{id}

Get a single collection with statistics (documents_count, chunks_count).

---

#### PATCH /api/v1/collections/{id}

Update a collection's name, description, or config.

---

#### DELETE /api/v1/collections/{id}

Delete a collection and all its documents.

---

### Authentication

#### POST /api/v1/auth/login

Authenticate and receive a JWT token.

**Request Body:**

| Field      | Type   | Required | Description        |
|------------|--------|----------|--------------------|
| `email`    | string | Yes      | User email address |
| `password` | string | Yes      | User password      |

**Response (200):**

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

---

#### POST /api/v1/auth/keys

Generate a new API key (admin only).

**Request Body:**

| Field             | Type   | Required | Description                  |
|-------------------|--------|----------|------------------------------|
| `name`            | string | Yes      | Human-readable key name      |
| `permissions`     | object | No       | Permission map               |
| `expires_in_days` | int    | No       | Days until expiry (null = never) |

**Response (201):**

```json
{
  "id": "...",
  "name": "Production Key",
  "key_prefix": "rtv_abc1",
  "raw_key": "rtv_abc123def456...",
  "permissions": {"query": true, "ingest": true},
  "created_at": "2025-01-15T10:00:00Z",
  "expires_at": null
}
```

The `raw_key` field is only returned on creation. Store it securely.

---

#### GET /api/v1/auth/keys

List all API keys for the current tenant (raw keys are not included).

---

#### DELETE /api/v1/auth/keys/{id}

Revoke an API key.

---

### Admin

#### GET /api/v1/admin/stats

Get platform-wide statistics (admin only).

#### GET /api/v1/admin/health

Health check endpoint. Returns service status for all dependencies.
