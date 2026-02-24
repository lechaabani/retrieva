"""Event hook system for plugin lifecycle and pipeline events."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Predefined hook names.
HOOK_NAMES = frozenset({
    "before_ingest",
    "after_ingest",
    "before_extract",
    "after_extract",
    "before_chunk",
    "after_chunk",
    "before_embed",
    "after_embed",
    "before_query",
    "after_query",
    "before_generate",
    "after_generate",
    "on_plugin_load",
    "on_plugin_unload",
    "on_error",
})


class HookManager:
    """Register and emit hooks."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def register(self, hook_name: str, handler: Callable) -> None:
        """Register *handler* to be called when *hook_name* fires."""
        if hook_name not in HOOK_NAMES:
            logger.warning("Registering handler for unknown hook '%s'", hook_name)
        self._handlers[hook_name].append(handler)

    def unregister(self, hook_name: str, handler: Callable) -> None:
        handlers = self._handlers.get(hook_name, [])
        if handler in handlers:
            handlers.remove(handler)

    async def emit(self, hook_name: str, **context: Any) -> None:
        """Fire all handlers registered for *hook_name*.

        Handlers may be sync or async.  Errors in a handler are logged
        but do not prevent subsequent handlers from running.
        """
        for handler in self._handlers.get(hook_name, []):
            try:
                result = handler(**context)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.warning(
                    "Hook handler %s for '%s' raised an exception",
                    handler,
                    hook_name,
                    exc_info=True,
                )

    def clear(self, hook_name: str | None = None) -> None:
        """Remove all handlers, or only those for *hook_name*."""
        if hook_name:
            self._handlers.pop(hook_name, None)
        else:
            self._handlers.clear()
