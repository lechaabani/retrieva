import { HttpClient } from "./client.js";
import type {
  WidgetConfig,
  WidgetQueryResponse,
  WidgetSearchOptions,
  WidgetSearchResponse,
} from "./types.js";
import { RetrievaError } from "./errors.js";

/**
 * Lightweight client for the Retrieva widget (public) endpoints.
 *
 * Intended for use in browser-based widgets or front-end apps that only need
 * query and search capabilities scoped to a specific widget ID.
 *
 * ```ts
 * const widget = new RetrievaWidget({
 *   apiKey: 'rtv_pub_xxx',
 *   widgetId: 'my-widget-id',
 * });
 * const { answer } = await widget.query('How does billing work?');
 * ```
 */
export class RetrievaWidget {
  private readonly client: HttpClient;
  private readonly widgetId: string;

  constructor(config: WidgetConfig) {
    if (!config.widgetId) {
      throw new RetrievaError("widgetId is required for the Widget client.");
    }

    this.widgetId = config.widgetId;
    this.client = new HttpClient({
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      timeout: config.timeout,
      headers: config.headers,
    });
  }

  /**
   * Ask a question through the widget endpoint.
   *
   * @param question - The natural-language question.
   * @returns The generated answer and source documents.
   */
  async query(question: string): Promise<WidgetQueryResponse> {
    return this.client.post<WidgetQueryResponse>("/widget/query", {
      question,
      widget_id: this.widgetId,
    });
  }

  /**
   * Perform a search through the widget endpoint.
   *
   * @param query   - The search query string.
   * @param options - Optional parameters (topK).
   * @returns Matching results.
   */
  async search(
    query: string,
    options: WidgetSearchOptions = {},
  ): Promise<WidgetSearchResponse> {
    const body: Record<string, unknown> = {
      query,
      widget_id: this.widgetId,
    };
    if (options.topK !== undefined) body.top_k = options.topK;

    return this.client.post<WidgetSearchResponse>("/widget/search", body);
  }
}
