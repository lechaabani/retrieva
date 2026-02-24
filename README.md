<div align="center">

# Retrieva

### The WordPress of RAG

The open-source platform to build, deploy, and scale Retrieval-Augmented Generation applications.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)

[Documentation](https://docs.retrieva.ai) · [Demo](https://demo.retrieva.ai) · [Discord](https://discord.gg/retrieva) · [retrieva.ai](https://retrieva.ai)

</div>

---

## Why Retrieva?

Building production RAG is hard. You start with a prototype, then spend months wiring up document parsing, chunking strategies, vector search, reranking, multi-tenancy, auth, and a UI. Retrieva gives you all of that out of the box.

- **Ship in minutes, not months.** Go from zero to a fully working RAG API with one `docker compose up`.
- **Every component is swappable.** Switch LLM providers, embedding models, or vector stores without rewriting your application.
- **Built for production from day one.** Multi-tenant isolation, API key management, rate limiting, and RBAC are included -- not afterthoughts.
- **Extend without forking.** A plugin system with 8 extension points lets you customize ingestion, retrieval, and generation without touching core code.

Like WordPress transformed web publishing, Retrieva transforms RAG -- making powerful AI retrieval accessible to every developer and organization.

---

## Features

### Core Engine
- 📄 **Multi-format ingestion** -- PDF, DOCX, XLSX, CSV, HTML, Markdown, and plain text
- 🔍 **Hybrid search** -- Combines vector similarity (Qdrant) with BM25 keyword matching
- 🤖 **10+ LLM providers** -- OpenAI, Anthropic, Cohere, local models via sentence-transformers, and more
- 🎯 **Cross-encoder reranking** -- Second-stage ranker for significantly improved result quality

### Plugin System
- 🔌 **8 plugin types** -- Extractors, chunkers, embedders, retrievers, generators, connectors, auth, and middleware
- 📦 **20+ built-in plugins** -- Ready-to-use components for common workflows
- 🛠️ **Custom plugin API** -- Build and distribute your own plugins with a simple interface

### Connectors
- ☁️ **10+ data sources** -- S3, Google Drive, Confluence, Notion, GitHub, Slack, PostgreSQL, web crawler, and more
- 🔄 **Automatic sync** -- Keep your knowledge base up-to-date with scheduled and webhook-triggered syncs

### Dashboard
- 📊 **Real-time analytics** -- Query latency, token usage, retrieval quality, and document coverage
- 🧪 **Playground** -- Test queries interactively and inspect retrieved chunks
- 📁 **Document explorer** -- Browse, search, and manage ingested documents
- 🗂️ **Collection management** -- Create and configure isolated knowledge bases

### Developer Experience
- 🌐 **REST API** -- Comprehensive API with OpenAPI docs at `/docs`
- 📚 **JS + Python SDKs** -- First-class client libraries for both ecosystems
- ⌨️ **CLI tool** -- Manage collections, ingest documents, and run queries from the terminal
- 🧩 **Embeddable widgets** -- Drop a search widget into any web page with a single script tag

### Enterprise Ready
- 🏢 **Multi-tenant architecture** -- Fully isolated collections with per-tenant configuration
- 🔑 **API key management** -- Scoped keys with granular permissions
- 🚦 **Rate limiting** -- Per-key and per-tenant rate limits out of the box
- 🛡️ **RBAC** -- Role-based access control with JWT and API key authentication

---

## Quick Start

Get Retrieva running locally in under two minutes:

```bash
git clone https://github.com/lechaabani/retrieva.git
cd retrieva
cp .env.example .env          # Add your OPENAI_API_KEY here
docker compose up -d
```

That's it. Open your browser:

| Service   | URL                          |
|-----------|------------------------------|
| Dashboard | http://localhost:3000         |
| API Docs  | http://localhost:8000/docs    |
| API       | http://localhost:8000/api/v1  |

Upload your first document:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your document text here...",
    "title": "My Document",
    "collection": "knowledge-base"
  }'
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is our refund policy?",
    "collection": "knowledge-base"
  }'
```

---

## Architecture

```
                        ┌──────────────┐
                        │   Dashboard  │
                        │  (Next.js)   │
                        │   :3000      │
                        └──────┬───────┘
                               │
    Clients ──────────► ┌──────┴───────┐
      SDKs              │   FastAPI    │
      CLI               │   REST API   │
      Widgets           │   :8000      │
                        └──┬───┬───┬───┘
                           │   │   │
              ┌────────────┘   │   └────────────┐
              ▼                ▼                 ▼
       ┌─────────────┐ ┌─────────────┐  ┌─────────────┐
       │ PostgreSQL   │ │   Qdrant    │  │    Redis     │
       │ Documents,   │ │   Vector    │  │  Cache &     │
       │ Users, Meta  │ │   Search    │  │  Task Broker │
       │ :5432        │ │   :6333     │  │  :6379       │
       └─────────────┘ └─────────────┘  └──────┬──────┘
                                                │
                                         ┌──────┴──────┐
                                         │   Celery    │
                                         │   Workers   │
                                         └──────┬──────┘
                                                │
                                   ┌────────────┼────────────┐
                                   ▼            ▼            ▼
                               Extract       Chunk        Embed
                             (PDF, DOCX,   (Semantic,   (OpenAI,
                              HTML, TXT)    Fixed)       Local)
```

**Stack:** Python 3.11+ / FastAPI / SQLAlchemy 2 / Celery / Qdrant / PostgreSQL / Redis / Next.js 14

---

## Configuration

Retrieva is configured through `config.yaml` with environment variable overrides:

```yaml
ingestion:
  chunking:
    strategy: semantic        # semantic | fixed | paragraph
    chunk_size: 512
    chunk_overlap: 50
  embedding:
    provider: openai          # openai | cohere | sentence-transformers
    model: text-embedding-3-small

retrieval:
  strategy: hybrid            # vector | keyword | hybrid
  top_k: 10
  reranking:
    enabled: true
    model: cross-encoder/ms-marco-MiniLM-L-6-v2

generation:
  provider: openai            # openai | anthropic | local
  model: gpt-4o
  temperature: 0.1
  max_tokens: 1024

vector_db:
  provider: qdrant
  url: http://qdrant:6333

connectors:
  s3:
    bucket: my-documents
    region: us-east-1
  google_drive:
    folder_id: "1a2b3c..."
```

See the full [Configuration Reference](docs/configuration.md).

---

## SDKs

### Python

```bash
pip install retrieva-sdk
```

```python
from retrieva import RetrievaClient

client = RetrievaClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Ingest a document
client.ingest.text(
    content="Your document content...",
    collection="knowledge-base"
)

# Query
response = client.query(
    question="What is our refund policy?",
    collection="knowledge-base"
)
print(response.answer)
```

### JavaScript / TypeScript

```bash
npm install @retrieva/sdk
```

```typescript
import { RetrievaClient } from "@retrieva/sdk";

const client = new RetrievaClient({
  baseUrl: "http://localhost:8000",
  apiKey: "your-api-key",
});

// Query
const response = await client.query({
  question: "What is our refund policy?",
  collection: "knowledge-base",
});
console.log(response.answer);
```

---

## Embeddable Widgets

Add a RAG-powered search widget to any website with a single script tag:

```html
<script
  src="https://cdn.retrieva.ai/widget.js"
  data-api-url="http://localhost:8000"
  data-api-key="your-public-key"
  data-collection="knowledge-base"
  data-theme="light"
></script>
```

The widget renders a search bar with streaming answers, source citations, and customizable styling.

---

## Self-Hosted vs Cloud

|                        | Self-Hosted (Free)         | Retrieva Cloud              |
|------------------------|----------------------------|-----------------------------|
| **License**            | MIT                        | Managed service             |
| **Infrastructure**     | You manage                 | Fully managed               |
| **Updates**            | Manual                     | Automatic                   |
| **Support**            | Community (GitHub, Discord)| Priority support + SLA      |
| **SSO / SAML**         | Configure yourself         | Built-in                    |
| **Analytics**          | Basic dashboard            | Advanced analytics + alerts |
| **Uptime SLA**         | --                         | 99.9%                       |
| **Price**              | Free forever               | Usage-based                 |

[Learn more about Retrieva Cloud →](https://retrieva.ai/pricing)

---

## Project Structure

```
retrieva/
  api/                    # FastAPI application
    routes/               #   API route handlers
    auth/                 #   API key and JWT authentication
    models/               #   SQLAlchemy ORM models
    schemas/              #   Pydantic request/response schemas
    middleware/           #   Rate limiting, logging, CORS
  core/                   # Core RAG engine
    ingestion/            #   Extraction, chunking, embedding pipeline
    retrieval/            #   Search engine, reranking, filters
    generation/           #   LLM generation, prompts, guardrails
    connectors/           #   Data source connectors
  workers/                # Celery background tasks
  plugins/                # Plugin directory
  dashboard/              # Next.js frontend
  tests/                  # Test suite (unit, integration, e2e)
  docs/                   # Documentation
  alembic/                # Database migrations
  docker-compose.yml      # Full stack definition
```

---

## Development

```bash
# Install dependencies
pip install -e ".[dev,test]"

# Run tests
pytest                     # All tests
pytest -m unit             # Unit tests only
pytest -m integration      # Integration tests (requires services)
pytest -m e2e              # End-to-end tests

# Lint and format
ruff check .
ruff format .

# Type check
mypy api core workers
```

---

## Contributing

Contributions are welcome and appreciated. Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`) and linting is clean (`ruff check .`)
5. Submit a pull request

Please read our [Contributing Guide](docs/CONTRIBUTING.md) for more details on code style, commit conventions, and the review process.

---

## License

Retrieva is open-source software licensed under the [MIT License](LICENSE).

---

<div align="center">

If you find Retrieva useful, please consider giving it a star. It helps others discover the project.

[Star Retrieva on GitHub](https://github.com/lechaabani/retrieva)

---

Built with care by the [Retrieva](https://retrieva.ai) team and contributors.

</div>
