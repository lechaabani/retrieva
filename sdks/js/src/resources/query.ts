import type { HttpClient } from "../client.js";
import type { QueryOptions, QueryResponse } from "../types.js";

export class QueryResource {
  private readonly client: HttpClient;

  constructor(client: HttpClient) {
    this.client = client;
  }

  /**
   * Ask a question and receive a generated answer with optional source documents.
   *
   * @param question  - The natural-language question to ask.
   * @param options   - Optional parameters (collectionId, topK, includeSources, language).
   * @returns A promise that resolves with the answer, sources, confidence, and usage info.
   */
  async execute(
    question: string,
    options: QueryOptions = {},
  ): Promise<QueryResponse> {
    const body: Record<string, unknown> = { question };
    if (options.collectionId !== undefined) body.collection_id = options.collectionId;
    if (options.topK !== undefined) body.top_k = options.topK;
    if (options.includeSources !== undefined) body.include_sources = options.includeSources;
    if (options.language !== undefined) body.language = options.language;

    return this.client.post<QueryResponse>("/api/v1/query", body);
  }
}
