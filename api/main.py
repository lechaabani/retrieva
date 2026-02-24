"""Retrieva RAG Platform API -- FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.database import engine, Base
from api.middleware.logging import RequestLoggingMiddleware
from api.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from api.routes import (
    activity_router,
    admin_router,
    analytics_dashboard_router,
    billing_router,
    collections_router,
    compare_router,
    documents_router,
    suggestions_router,
    eval_router,
    ingest_router,
    plugins_router,
    query_router,
    setup_router,
    sources_router,
    templates_router,
    widget_admin_router,
    widget_router,
)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("retrieva.api")

# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ---------------------------------------------------------------------------
# Lifespan events
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # -- Startup --------------------------------------------------------
    logger.info("Starting Retrieva API ...")

    # Create tables if they don't exist (for development; use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")

    # Initialise vector store connection
    try:
        from core.vector_store import VectorStore

        vs = VectorStore()
        await vs.initialize()
        logger.info("Vector store connection established.")
    except Exception:
        logger.warning("Vector store not available at startup -- queries may fail.")

    # Initialise plugin manager
    try:
        from core.plugin_system.manager import get_plugin_manager

        plugin_manager = get_plugin_manager()
        plugin_manager.initialize()
        app.state.plugin_manager = plugin_manager
        logger.info("Plugin manager initialised.")
    except Exception:
        logger.warning("Plugin manager failed to initialise -- plugins may be unavailable.")

    yield

    # -- Shutdown -------------------------------------------------------
    logger.info("Shutting down Retrieva API ...")
    await engine.dispose()
    logger.info("Database connections closed.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Retrieva - RAG Platform API",
    description=(
        "Production-grade Retrieval-Augmented Generation platform. "
        "Ingest documents, search semantically, and generate answers grounded in your data."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# -- State / extensions ----------------------------------------------------
app.state.limiter = limiter

# -- Middleware (order matters: last added = first executed) ----------------
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Exception handlers ----------------------------------------------------
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# -- Routers ---------------------------------------------------------------
API_V1 = "/api/v1"

app.include_router(query_router, prefix=API_V1)
app.include_router(ingest_router, prefix=API_V1)
app.include_router(documents_router, prefix=API_V1)
app.include_router(collections_router, prefix=API_V1)
app.include_router(admin_router, prefix=API_V1)
app.include_router(plugins_router, prefix=API_V1)
app.include_router(sources_router, prefix=API_V1)
app.include_router(setup_router, prefix=API_V1)
app.include_router(widget_admin_router, prefix=API_V1)
app.include_router(templates_router, prefix=API_V1)
app.include_router(eval_router, prefix=API_V1)
app.include_router(activity_router, prefix=API_V1)
app.include_router(compare_router, prefix=API_V1)
app.include_router(suggestions_router, prefix=API_V1)
app.include_router(analytics_dashboard_router, prefix=API_V1)
app.include_router(billing_router, prefix=API_V1)

# Widget public endpoints at root (clean URLs: /widget/chatbot.js)
app.include_router(widget_router)


# -- Root health check -----------------------------------------------------
@app.get("/", tags=["Health"], summary="Root Health Check")
async def root() -> dict:
    """Minimal health probe at the root path."""
    return {
        "service": "retrieva",
        "status": "ok",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health Check")
async def health() -> dict:
    """Health check endpoint for Docker and load balancers."""
    return {"status": "ok"}
