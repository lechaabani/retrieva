# retrieva-js

Official JavaScript/TypeScript SDK for the [Retrieva](https://github.com/retrieva) RAG platform.

- Zero dependencies -- uses the native `fetch()` API
- Works in Node.js 18+ and modern browsers
- Full TypeScript types included
- Supports both ESM and CommonJS

## Installation

```bash
npm install retrieva-js
```

## Quick start

```ts
import { Retrieva } from "retrieva-js";

const rag = new Retrieva({
  apiKey: "rtv_xxx",
  baseUrl: "https://api.example.com", // optional, defaults to http://localhost:8000
});

const result = await rag.query("How do I configure single sign-on?", {
  collectionId: "col_abc123",
  topK: 5,
  includeSources: true,
});

console.log(result.answer);
console.log(result.sources);
console.log(result.confidence);
```

## API reference

### Constructor

```ts
new Retrieva(config: RetrievaConfig)
```

| Option    | Type                       | Required | Default                  |
| --------- | -------------------------- | -------- | ------------------------ |
| apiKey    | `string`                   | Yes      |                          |
| baseUrl   | `string`                   | No       | `http://localhost:8000`  |
| timeout   | `number` (ms)              | No       | `30000`                  |
| headers   | `Record<string, string>`   | No       | `{}`                     |

### `rag.query(question, options?)`

Ask a question and receive a generated answer.

```ts
const result = await rag.query("What is the refund policy?", {
  collectionId: "col_abc",
  topK: 5,
  includeSources: true,
  language: "en",
});

// result.answer        - string
// result.sources       - Source[]
// result.confidence    - number
// result.latency_ms    - number
// result.tokens_used   - number
```

### `rag.search(query, options?)`

Perform a semantic search over your documents.

```ts
const hits = await rag.search("billing documentation", { topK: 10 });

for (const r of hits.results) {
  console.log(r.score, r.content);
}
```

### `rag.ingest.file(data, fileName, options)`

Upload a file for ingestion.

```ts
import { readFile } from "node:fs/promises";

const pdf = await readFile("./guide.pdf");
const res = await rag.ingest.file(pdf, "guide.pdf", {
  collection: "docs",
  metadata: { author: "Jane" },
});
console.log(res.document_id);
```

### `rag.ingest.text(content, title, options)`

Ingest a plain-text document.

```ts
await rag.ingest.text("Full article body here...", "My Article", {
  collection: "docs",
});
```

### `rag.ingest.url(url, options)`

Ingest content from a URL.

```ts
await rag.ingest.url("https://example.com/docs", {
  collection: "docs",
  crawlDepth: 2,
});
```

### `rag.collections.list()`

List all collections.

```ts
const collections = await rag.collections.list();
```

### `rag.collections.get(id)`

Retrieve a single collection.

```ts
const col = await rag.collections.get("col_abc");
```

### `rag.collections.create(body)`

Create a new collection.

```ts
const col = await rag.collections.create({
  name: "docs",
  description: "Product documentation",
  embedding_model: "text-embedding-3-small",
});
```

### `rag.collections.update(id, body)`

Update a collection.

```ts
await rag.collections.update("col_abc", { description: "Updated description" });
```

### `rag.collections.delete(id)`

Delete a collection.

```ts
await rag.collections.delete("col_abc");
```

## Widget client

For public/embeddable use cases (e.g. a chat widget on your website) use the
lightweight Widget client. It only exposes `query` and `search` and targets the
`/widget/*` endpoints.

```ts
import { Retrieva } from "retrieva-js";

const widget = new Retrieva.Widget({
  apiKey: "rtv_pub_xxx",
  widgetId: "wgt_abc123",
  baseUrl: "https://api.example.com",
});

const { answer, sources } = await widget.query("How does pricing work?");
const { results } = await widget.search("pricing", { topK: 5 });
```

## Error handling

All API errors are thrown as typed exceptions that extend `RetrievaError`.

```ts
import {
  RetrievaError,
  AuthenticationError,
  NotFoundError,
  RateLimitError,
} from "retrieva-js";

try {
  await rag.query("test");
} catch (err) {
  if (err instanceof AuthenticationError) {
    console.error("Bad API key");
  } else if (err instanceof RateLimitError) {
    console.error("Slow down -- retry after a moment");
  } else if (err instanceof NotFoundError) {
    console.error("Resource not found");
  } else if (err instanceof RetrievaError) {
    console.error(err.status, err.message, err.body);
  }
}
```

| Error class           | HTTP status | When                          |
| --------------------- | ----------- | ----------------------------- |
| `AuthenticationError` | 401         | Invalid or missing API key    |
| `PermissionError`     | 403         | Insufficient permissions      |
| `NotFoundError`       | 404         | Resource does not exist        |
| `ValidationError`     | 422         | Invalid request body          |
| `RateLimitError`      | 429         | Too many requests             |
| `ServerError`         | 5xx         | Server-side failure           |
| `TimeoutError`        | --          | Request exceeded timeout      |
| `ConnectionError`     | --          | Network / DNS failure         |
| `RetrievaError`       | any         | Base class for all errors     |

Every error instance exposes `.status` (number or undefined) and `.body`
(parsed JSON response, if available).

## Building from source

```bash
npm install
npm run build
```

This produces `dist/esm/` (ES modules) and `dist/cjs/` (CommonJS).

## License

MIT
