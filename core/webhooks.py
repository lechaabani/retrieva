"""Webhook dispatching system for event notifications.

Sends HTTP POST requests to registered webhook URLs when platform events
occur (document indexed, document deleted, query completed, etc.).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Supported event types
WEBHOOK_EVENTS = frozenset({
    "document_indexed",
    "document_deleted",
    "document_error",
    "query_completed",
    "connector_sync_completed",
})

# HTTP client settings
_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
_MAX_RETRIES = 3


class WebhookDispatcher:
    """Dispatches event notifications to registered webhook endpoints.

    Loads webhook registrations from the database and sends HTTP POST
    payloads with event data.  Uses httpx with configurable timeouts and
    automatic retries.
    """

    def __init__(self, tenant_id: str | None = None) -> None:
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        event: str,
        data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Send an event notification to all matching webhooks.

        Args:
            event: Event name (must be one of ``WEBHOOK_EVENTS``).
            data: Arbitrary payload data for the event.
            tenant_id: Override tenant scope (falls back to ``self.tenant_id``).

        Returns:
            A list of result dicts, one per webhook, with delivery status.
        """
        effective_tenant = tenant_id or self.tenant_id
        if not effective_tenant:
            logger.warning("Cannot dispatch webhook: no tenant_id provided")
            return []

        if event not in WEBHOOK_EVENTS:
            logger.warning("Unknown webhook event: %s", event)
            return []

        webhooks = await self._load_webhooks(effective_tenant, event)
        if not webhooks:
            return []

        payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for wh in webhooks:
                result = await self._send_webhook(client, wh, payload)
                results.append(result)

        return results

    def dispatch_sync(
        self,
        event: str,
        data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Synchronous wrapper around ``dispatch`` for use in Celery workers."""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.dispatch(event, data, tenant_id=tenant_id)
            )
        finally:
            loop.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _load_webhooks(
        tenant_id: str, event: str
    ) -> list[dict[str, Any]]:
        """Load active webhook registrations from the database.

        First attempts to load from the dedicated ``webhooks`` table.  If the
        model is not available (e.g. table not yet migrated), falls back to
        the tenant config JSONB approach used by the existing admin endpoint.
        """
        webhooks: list[dict[str, Any]] = []

        try:
            from workers.db import get_sync_session
            from api.models.webhook import Webhook

            with get_sync_session() as session:
                rows = (
                    session.query(Webhook)
                    .filter(
                        Webhook.tenant_id == uuid.UUID(tenant_id),
                        Webhook.active.is_(True),
                    )
                    .all()
                )
                for row in rows:
                    if event in (row.events or []):
                        webhooks.append({
                            "id": str(row.id),
                            "url": row.url,
                            "events": row.events,
                        })
        except Exception:
            # Fallback: read from tenant config JSONB
            try:
                from workers.db import get_sync_session
                from api.models.tenant import Tenant

                with get_sync_session() as session:
                    tenant = session.get(Tenant, uuid.UUID(tenant_id))
                    if tenant and tenant.config:
                        for wh in tenant.config.get("webhooks", []):
                            if wh.get("active", True) and event in wh.get("events", []):
                                webhooks.append(wh)
            except Exception as exc:
                logger.error("Failed to load webhooks: %s", exc)

        return webhooks

    @staticmethod
    async def _send_webhook(
        client: httpx.AsyncClient,
        webhook: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a single webhook notification with retries.

        Args:
            client: An open httpx.AsyncClient.
            webhook: Webhook dict with at least ``url`` and ``id`` keys.
            payload: JSON-serialisable payload to POST.

        Returns:
            A result dict with ``webhook_id``, ``status``, and optional ``error``.
        """
        url = webhook["url"]
        webhook_id = webhook.get("id", "unknown")
        body = json.dumps(payload, default=str)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Retrieva-Webhook/1.0",
            "X-Webhook-Event": payload.get("event", ""),
        }

        # HMAC signature if secret is configured
        secret = webhook.get("secret")
        if secret:
            signature = hmac.new(
                secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        last_error: str | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await client.post(url, content=body, headers=headers)
                if response.status_code < 400:
                    logger.info(
                        "Webhook delivered: id=%s url=%s status=%d",
                        webhook_id, url, response.status_code,
                    )
                    return {
                        "webhook_id": webhook_id,
                        "status": "delivered",
                        "status_code": response.status_code,
                    }
                else:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(
                        "Webhook HTTP error: id=%s url=%s status=%d attempt=%d/%d",
                        webhook_id, url, response.status_code, attempt, _MAX_RETRIES,
                    )
            except httpx.TimeoutException as exc:
                last_error = f"Timeout: {exc}"
                logger.warning(
                    "Webhook timeout: id=%s url=%s attempt=%d/%d",
                    webhook_id, url, attempt, _MAX_RETRIES,
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Webhook error: id=%s url=%s attempt=%d/%d error=%s",
                    webhook_id, url, attempt, _MAX_RETRIES, exc,
                )

        logger.error(
            "Webhook delivery failed after %d attempts: id=%s url=%s error=%s",
            _MAX_RETRIES, webhook_id, url, last_error,
        )
        return {
            "webhook_id": webhook_id,
            "status": "failed",
            "error": last_error,
        }
