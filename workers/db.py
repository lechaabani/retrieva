"""Synchronous database access for Celery workers.

Celery workers run outside the asyncio event loop, so they must use
synchronous SQLAlchemy engines and sessions. This module mirrors the
async setup in ``api.database`` but uses psycopg2 (via the default
``postgresql://`` scheme).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://retrieva:retrieva@localhost:5432/retrieva",
)

# Convert asyncpg URL to sync psycopg2 URL for worker use.
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "").replace(
    "postgresql://", "postgresql+psycopg2://"
) if "+asyncpg" in DATABASE_URL else DATABASE_URL

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Yield a synchronous SQLAlchemy session with automatic cleanup.

    Usage::

        with get_sync_session() as session:
            doc = session.get(Document, doc_id)
            doc.status = DocumentStatus.INDEXED
            session.commit()
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
