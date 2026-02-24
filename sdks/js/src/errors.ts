import type { ErrorResponseBody } from "./types.js";

/**
 * Base error class for all Retrieva SDK errors.
 */
export class RetrievaError extends Error {
  /** HTTP status code, if the error originated from an HTTP response. */
  public readonly status: number | undefined;
  /** Parsed response body, when available. */
  public readonly body: ErrorResponseBody | undefined;

  constructor(
    message: string,
    status?: number,
    body?: ErrorResponseBody,
  ) {
    super(message);
    this.name = "RetrievaError";
    this.status = status;
    this.body = body;

    // Maintain proper prototype chain in transpiled output.
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Raised when the API returns 401 Unauthorized.
 */
export class AuthenticationError extends RetrievaError {
  constructor(message?: string, body?: ErrorResponseBody) {
    super(
      message ?? "Authentication failed. Check your API key.",
      401,
      body,
    );
    this.name = "AuthenticationError";
  }
}

/**
 * Raised when the API returns 403 Forbidden.
 */
export class PermissionError extends RetrievaError {
  constructor(message?: string, body?: ErrorResponseBody) {
    super(
      message ?? "You do not have permission to perform this action.",
      403,
      body,
    );
    this.name = "PermissionError";
  }
}

/**
 * Raised when the API returns 404 Not Found.
 */
export class NotFoundError extends RetrievaError {
  constructor(message?: string, body?: ErrorResponseBody) {
    super(message ?? "The requested resource was not found.", 404, body);
    this.name = "NotFoundError";
  }
}

/**
 * Raised when the API returns 422 Validation Error.
 */
export class ValidationError extends RetrievaError {
  constructor(message?: string, body?: ErrorResponseBody) {
    super(message ?? "Validation error.", 422, body);
    this.name = "ValidationError";
  }
}

/**
 * Raised when the API returns 429 Too Many Requests.
 */
export class RateLimitError extends RetrievaError {
  constructor(message?: string, body?: ErrorResponseBody) {
    super(message ?? "Rate limit exceeded. Please retry later.", 429, body);
    this.name = "RateLimitError";
  }
}

/**
 * Raised when the API returns a 5xx status code.
 */
export class ServerError extends RetrievaError {
  constructor(message?: string, status?: number, body?: ErrorResponseBody) {
    super(message ?? "Internal server error.", status ?? 500, body);
    this.name = "ServerError";
  }
}

/**
 * Raised when the request times out.
 */
export class TimeoutError extends RetrievaError {
  constructor(message?: string) {
    super(message ?? "Request timed out.");
    this.name = "TimeoutError";
  }
}

/**
 * Raised when a network-level error occurs (DNS failure, connection refused, etc.).
 */
export class ConnectionError extends RetrievaError {
  constructor(message?: string) {
    super(message ?? "Unable to connect to the Retrieva API.");
    this.name = "ConnectionError";
  }
}
