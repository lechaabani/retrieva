"""Celery application configuration for the Retrieva platform.

Configures broker, result backend, task routing, serialization,
and periodic beat schedules for background ingestion and sync tasks.
"""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

# ---------------------------------------------------------------------------
# Broker & result backend
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery("retrieva")

app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Result expiration (24 hours)
    result_expires=86400,
    # Task routing
    task_routes={
        "workers.ingestion_worker.*": {"queue": "ingestion"},
        "workers.sync_worker.*": {"queue": "sync"},
    },
    task_default_queue="default",
    # Task discovery
    include=[
        "workers.ingestion_worker",
        "workers.sync_worker",
    ],
)

# ---------------------------------------------------------------------------
# Beat schedule — periodic tasks
# ---------------------------------------------------------------------------

SYNC_INTERVAL_HOURS = int(os.getenv("SYNC_INTERVAL_HOURS", "6"))

app.conf.beat_schedule = {
    "sync-all-sources-periodic": {
        "task": "workers.sync_worker.sync_all_sources_periodic",
        "schedule": crontab(minute=0, hour=f"*/{SYNC_INTERVAL_HOURS}"),
        "options": {"queue": "sync"},
    },
    "check-pending-syncs": {
        "task": "workers.sync_worker.check_pending_syncs",
        "schedule": 300.0,  # every 5 minutes
        "options": {"queue": "sync"},
    },
}
