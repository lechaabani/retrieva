import type { HttpClient } from "../client.js";
import type {
  IngestFileOptions,
  IngestTextOptions,
  IngestUrlOptions,
  IngestResponse,
} from "../types.js";

export class IngestResource {
  private readonly client: HttpClient;

  constructor(client: HttpClient) {
    this.client = client;
  }

  /**
   * Ingest a file (PDF, DOCX, TXT, etc.) into a collection.
   *
   * In **Node.js 18+** pass a `Buffer` or `Uint8Array` as `fileData`.
   * In the **browser** you may pass a `Blob` or `File` directly.
   *
   * @param fileData - The file contents (Buffer, Uint8Array, Blob, or File).
   * @param fileName - The original file name (e.g. "guide.pdf").
   * @param options  - Must include `collection`. Optionally include `metadata`.
   */
  async file(
    fileData: Blob | Buffer | Uint8Array,
    fileName: string,
    options: IngestFileOptions,
  ): Promise<IngestResponse> {
    const form = new FormData();

    // Normalise to Blob for cross-runtime compatibility.
    const blob =
      fileData instanceof Blob
        ? fileData
        : new Blob([fileData]);

    form.append("file", blob, fileName);
    form.append("collection", options.collection);
    if (options.metadata !== undefined) {
      form.append("metadata", JSON.stringify(options.metadata));
    }

    return this.client.postForm<IngestResponse>("/api/v1/ingest", form);
  }

  /**
   * Ingest a plain-text document into a collection.
   *
   * @param content - The text content to ingest.
   * @param title   - A human-readable title for the document.
   * @param options - Must include `collection`. Optionally include `metadata`.
   */
  async text(
    content: string,
    title: string,
    options: IngestTextOptions,
  ): Promise<IngestResponse> {
    const body: Record<string, unknown> = {
      content,
      title,
      collection: options.collection,
    };
    if (options.metadata !== undefined) body.metadata = options.metadata;

    return this.client.post<IngestResponse>("/api/v1/ingest/text", body);
  }

  /**
   * Ingest content from a URL (with optional crawling).
   *
   * @param url     - The URL to fetch and ingest.
   * @param options - Must include `collection`. Optionally include `crawlDepth`.
   */
  async url(
    url: string,
    options: IngestUrlOptions,
  ): Promise<IngestResponse> {
    const body: Record<string, unknown> = {
      url,
      collection: options.collection,
    };
    if (options.crawlDepth !== undefined) body.crawl_depth = options.crawlDepth;

    return this.client.post<IngestResponse>("/api/v1/ingest/url", body);
  }
}
