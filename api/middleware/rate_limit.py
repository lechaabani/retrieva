"""Rate limiting middleware using slowapi."""

import os

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

DEFAULT_QUERY_LIMIT = os.getenv("RATE_LIMIT_QUERY", "100/minute")
DEFAULT_SEARCH_LIMIT = os.getenv("RATE_LIMIT_SEARCH", "1000/minute")
DEFAULT_INGEST_LIMIT = os.getenv("RATE_LIMIT_INGEST", "50/minute")
DEFAULT_ADMIN_LIMIT = os.getenv("RATE_LIMIT_ADMIN", "200/minute")


def _key_func(request: Request) -> str:
    """Extract rate-limit key from request.

    Prefers the API key (from the Authorization header) so that limits are
    per-tenant.  Falls back to the client IP address for unauthenticated
    requests.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use first 16 chars of key as bucket identifier (enough to be unique,
        # avoids storing the full key in the limiter backend).
        return auth_header[7:23]
    return get_remote_address(request)


limiter = Limiter(
    key_func=_key_func,
    default_limits=["200/minute"],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> Response:
    """Return a JSON 429 response when rate limits are exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail,
        },
    )
