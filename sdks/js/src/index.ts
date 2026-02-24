import { HttpClient } from "./client.js";
import { QueryResource } from "./resources/query.js";
import { SearchResource } from "./resources/search.js";
import { IngestResource } from "./resources/ingest.js";
import { CollectionsResource } from "./resources/collections.js";
import { RetrievaWidget } from "./widget.js";
import type {
  RetrievaConfig,
  QueryOptions,
  QueryResponse,
  SearchOptions,
  SearchResponse,
} from "./types.js";

/**
 * Main SDK client for the Retrieva RAG platform.
 *
 * ```ts
 * import { Retrieva } from 'retrieva-js';
 *
 * const rag = new Retrieva({ apiKey: 'rtv_xxx' });
 *
 * const result = await rag.query('How to configure X?');
 * console.log(result.answer);
 * ```
 */
export class Retrieva {
  private readonly _client: HttpClient;
  private readonly _query: QueryResource;
  private readonly _search: SearchResource;

  /** Ingest resources (file, text, url). */
  public readonly ingest: IngestResource;
  /** Collection CRUD operations. */
  public readonly collections: CollectionsResource;

  /**
   * Widget client constructor, exposed as a static property for convenient access.
   *
   * ```ts
   * const widget = new Retrieva.Widget({ apiKey: 'rtv_pub_xxx', widgetId: 'id' });
   * ```
   */
  static Widget = RetrievaWidget;

  constructor(config: RetrievaConfig) {
    this._client = new HttpClient({
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      timeout: config.timeout,
      headers: config.headers,
    });

    this._query = new QueryResource(this._client);
    this._search = new SearchResource(this._client);
    this.ingest = new IngestResource(this._client);
    this.collections = new CollectionsResource(this._client);
  }

  /**
   * Ask a question and receive a generated answer with optional source documents.
   *
   * @param question  - The natural-language question.
   * @param options   - Optional parameters (collectionId, topK, includeSources, language).
   */
  async query(question: string, options?: QueryOptions): Promise<QueryResponse> {
    return this._query.execute(question, options);
  }

  /**
   * Perform a semantic search across ingested documents.
   *
   * @param query   - The search query string.
   * @param options - Optional parameters (collectionId, topK).
   */
  async search(query: string, options?: SearchOptions): Promise<SearchResponse> {
    return this._search.execute(query, options);
  }
}

// ---------------------------------------------------------------------------
// Re-exports
// ---------------------------------------------------------------------------

export { RetrievaWidget } from "./widget.js";
export { HttpClient } from "./client.js";

// Errors
export {
  RetrievaError,
  AuthenticationError,
  PermissionError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  TimeoutError,
  ConnectionError,
} from "./errors.js";

// Types
export type {
  RetrievaConfig,
  WidgetConfig,
  QueryOptions,
  QueryResponse,
  Source,
  SearchOptions,
  SearchResponse,
  SearchResult,
  IngestFileOptions,
  IngestTextOptions,
  IngestUrlOptions,
  IngestResponse,
  Collection,
  CreateCollectionBody,
  UpdateCollectionBody,
  CollectionListResponse,
  WidgetQueryResponse,
  WidgetSearchOptions,
  WidgetSearchResponse,
  ErrorResponseBody,
} from "./types.js";
