import type { RequestOptions, ErrorResponseBody } from "./types.js";
import {
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

const DEFAULT_BASE_URL = "http://localhost:8000";
const DEFAULT_TIMEOUT = 30_000;
const USER_AGENT = "retrieva-js/1.0.0";

export class HttpClient {
  public readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeout: number;
  private readonly extraHeaders: Record<string, string>;

  constructor(opts: {
    apiKey: string;
    baseUrl?: string;
    timeout?: number;
    headers?: Record<string, string>;
  }) {
    if (!opts.apiKey) {
      throw new RetrievaError("apiKey is required.");
    }
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeout = opts.timeout ?? DEFAULT_TIMEOUT;
    this.extraHeaders = opts.headers ?? {};
  }

  // ---------------------------------------------------------------------------
  // Public request helpers
  // ---------------------------------------------------------------------------

  async get<T>(path: string, query?: RequestOptions["query"]): Promise<T> {
    return this.request<T>({ method: "GET", path, query });
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>({ method: "POST", path, body });
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>({ method: "PUT", path, body });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>({ method: "DELETE", path });
  }

  /**
   * Send a multipart/form-data request. The caller provides a FormData instance.
   */
  async postForm<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>({
      method: "POST",
      path,
      body: formData,
      rawBody: true,
    });
  }

  // ---------------------------------------------------------------------------
  // Core request method
  // ---------------------------------------------------------------------------

  async request<T>(opts: RequestOptions): Promise<T> {
    const url = this.buildUrl(opts.path, opts.query);

    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      "User-Agent": USER_AGENT,
      ...this.extraHeaders,
      ...(opts.headers ?? {}),
    };

    // JSON body — set content-type. For FormData (rawBody) the browser / Node
    // runtime will set the correct multipart boundary automatically.
    let requestBody: BodyInit | undefined;
    if (opts.rawBody && opts.body !== undefined) {
      requestBody = opts.body as BodyInit;
    } else if (opts.body !== undefined) {
      headers["Content-Type"] = "application/json";
      requestBody = JSON.stringify(opts.body);
    }

    const timeout = opts.timeout ?? this.timeout;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    let response: Response;
    try {
      response = await fetch(url, {
        method: opts.method,
        headers,
        body: requestBody,
        signal: controller.signal,
      });
    } catch (err: unknown) {
      clearTimeout(timer);
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new TimeoutError(`Request to ${opts.path} timed out after ${timeout}ms.`);
      }
      const msg = err instanceof Error ? err.message : String(err);
      throw new ConnectionError(`Network error: ${msg}`);
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      await this.handleErrorResponse(response);
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    const data: T = await response.json();
    return data;
  }

  // ---------------------------------------------------------------------------
  // Internal
  // ---------------------------------------------------------------------------

  private buildUrl(
    path: string,
    query?: Record<string, string | number | boolean | undefined>,
  ): string {
    const base = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    if (!query) return base;

    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        params.set(key, String(value));
      }
    }
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
  }

  private async handleErrorResponse(response: Response): Promise<never> {
    let body: ErrorResponseBody | undefined;
    try {
      body = (await response.json()) as ErrorResponseBody;
    } catch {
      // response may not be JSON
    }

    const detail =
      body?.detail ?? body?.message ?? response.statusText ?? "Unknown error";
    const message = `[${response.status}] ${detail}`;

    switch (response.status) {
      case 401:
        throw new AuthenticationError(message, body);
      case 403:
        throw new PermissionError(message, body);
      case 404:
        throw new NotFoundError(message, body);
      case 422:
        throw new ValidationError(message, body);
      case 429:
        throw new RateLimitError(message, body);
      default:
        if (response.status >= 500) {
          throw new ServerError(message, response.status, body);
        }
        throw new RetrievaError(message, response.status, body);
    }
  }
}
