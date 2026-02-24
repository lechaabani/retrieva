# Getting Started with Retrieva

This guide walks you through installing Retrieva, running it locally, and making your first queries.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Docker** >= 24.0 and **Docker Compose** >= 2.20
- **Python** >= 3.11 (only needed for local development without Docker)
- An **OpenAI API key** (or Anthropic API key, depending on your provider choice)

Optional:

- **Git** for cloning the repository
- **curl** or **httpx** for testing API endpoints

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/retrieva.git
cd retrieva
```

### 2. Create your configuration

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to set your preferences. At minimum, you need to configure the LLM provider:

```yaml
generation:
  provider: openai
  model: gpt-4o-mini
```

### 3. Set environment variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional overrides
JWT_SECRET_KEY=your-secure-random-string
POSTGRES_PASSWORD=your-db-password
```

### 4. Start the platform

```bash
docker-compose up -d
```

This starts all services:

| Service       | Port  | Description                     |
|---------------|-------|---------------------------------|
| API           | 8000  | FastAPI application server      |
| Dashboard     | 3000  | Next.js management UI           |
| PostgreSQL    | 5432  | Relational database             |
| Qdrant        | 6333  | Vector database                 |
| Redis         | 6379  | Cache and task broker           |
| Celery Worker | --    | Background ingestion processing |

Verify the API is running:

```bash
curl http://localhost:8000/health
```

## First Steps

### Generate an API key

Before making requests, you need an API key. Use the admin endpoint or the dashboard to create one.

### Upload your first document

Upload a text document to a collection:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Retrieva is an open-source RAG platform. It supports PDF, DOCX, TXT, HTML, and CSV file formats. The platform uses hybrid search combining vector similarity with BM25 keyword matching.",
    "title": "About Retrieva",
    "collection": "my-docs"
  }'
```

Upload a file:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@/path/to/document.pdf" \
  -F "collection=my-docs"
```

### Query your documents

Once the document is indexed (status changes to `indexed`), you can query it:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What file formats does Retrieva support?",
    "collection": "my-docs"
  }'
```

Example response:

```json
{
  "answer": "Retrieva supports PDF, DOCX, TXT, HTML, and CSV file formats.",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "title": "About Retrieva",
      "content": "Retrieva is an open-source RAG platform...",
      "score": 0.94
    }
  ],
  "confidence": 0.94,
  "tokens_used": 87
}
```

### Perform a semantic search

If you only want retrieval without generation:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "file formats",
    "collection": "my-docs",
    "top_k": 5
  }'
```

## Next Steps

- Read the [Configuration Guide](./configuration.md) for detailed config options
- Explore the [API Reference](./api-reference.md) for all available endpoints
- Set up [Connectors](./connectors.md) to sync external data sources
- Review the [Deployment Guide](./deployment.md) for production setups
