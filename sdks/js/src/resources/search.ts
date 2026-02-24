import type { HttpClient } from "../client.js";
import type { SearchOptions, SearchResponse } from "../types.js";

export class SearchResource {
  private readonly client: HttpClient;

  constructor(client: HttpClient) {
    this.client = client;
  }

  /**
   * Perform a semantic search across ingested documents.
   *
   * @param query   - The search query string.
   * @param options - Optional parameters (collectionId, topK).
   * @returns A promise that resolves with matching results, total count, and latency.
   */
  async execute(
    query: string,
    options: SearchOptions = {},
  ): Promise<SearchResponse> {
    const body: Record<string, unknown> = { query };
    if (options.collectionId !== undefined) body.collection_id = options.collectionId;
    if (options.topK !== undefined) body.top_k = options.topK;

    return this.client.post<SearchResponse>("/api/v1/search", body);
  }
}
