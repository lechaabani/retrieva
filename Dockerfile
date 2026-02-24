# ============================================================================
# Retrieva - Multi-stage Dockerfile
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder - install dependencies in a clean layer
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY api/ ./api/
COPY core/ ./core/
COPY workers/ ./workers/
COPY plugins/ ./plugins/

RUN pip install --prefix=/install .

# ---------------------------------------------------------------------------
# Stage 2: Production - minimal runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY api/ ./api/
COPY core/ ./core/
COPY workers/ ./workers/
COPY plugins/ ./plugins/
COPY templates/ ./templates/

RUN mkdir -p /data/documents && \
    chown -R appuser:appuser /app /data/documents

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
