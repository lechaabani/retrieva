// ---------------------------------------------------------------------------
// Client configuration
// ---------------------------------------------------------------------------

export interface RetrievaConfig {
  apiKey: string;
  baseUrl?: string;
  /** Default timeout in milliseconds. Defaults to 30 000. */
  timeout?: number;
  /** Extra headers merged into every request. */
  headers?: Record<string, string>;
}

export interface WidgetConfig {
  apiKey: string;
  widgetId: string;
  baseUrl?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// ---------------------------------------------------------------------------
// HTTP layer
// ---------------------------------------------------------------------------

export interface RequestOptions {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  path: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  /** Override the default timeout for this single request. */
  timeout?: number;
  /** When true the body is sent as-is (used for FormData). */
  rawBody?: boolean;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export interface QueryOptions {
  collectionId?: string;
  topK?: number;
  includeSources?: boolean;
  language?: string;
}

export interface Source {
  content: string;
  score: number;
  metadata: Record<string, unknown>;
  document_id: string;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  confidence: number;
  latency_ms: number;
  tokens_used: number;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SearchOptions {
  collectionId?: string;
  topK?: number;
}

export interface SearchResult {
  content: string;
  score: number;
  metadata: Record<string, unknown>;
  document_id: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  latency_ms: number;
}

// ---------------------------------------------------------------------------
// Ingest
// ---------------------------------------------------------------------------

export interface IngestFileOptions {
  collection: string;
  metadata?: Record<string, unknown>;
}

export interface IngestTextOptions {
  collection: string;
  metadata?: Record<string, unknown>;
}

export interface IngestUrlOptions {
  collection: string;
  crawlDepth?: number;
}

export interface IngestResponse {
  document_id: string;
  status: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

export interface Collection {
  id: string;
  name: string;
  description?: string;
  embedding_model?: string;
  document_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCollectionBody {
  name: string;
  description?: string;
  embedding_model?: string;
}

export interface UpdateCollectionBody {
  name?: string;
  description?: string;
  embedding_model?: string;
}

export interface CollectionListResponse {
  collections: Collection[];
}

// ---------------------------------------------------------------------------
// Widget
// ---------------------------------------------------------------------------

export interface WidgetQueryResponse {
  answer: string;
  sources: Source[];
}

export interface WidgetSearchOptions {
  topK?: number;
}

export interface WidgetSearchResponse {
  results: SearchResult[];
  total: number;
  latency_ms: number;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export interface ErrorResponseBody {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}
