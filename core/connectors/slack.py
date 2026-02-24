"""Slack connector using the Slack Web API (Bot tokens)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)

_SLACK_BASE = "https://slack.com/api"


class SlackConnector(BaseConnector):
    """Connector for Slack workspaces via the Slack Web API.

    Supports:
    * Fetching message history from specific channels.
    * Fetching all public channels the bot is a member of.
    * Extracting full thread replies.
    * Filtering by date range.
    * Pagination through long histories.

    Required bot token scopes: channels:history, channels:read,
    groups:history (for private channels), users:read (for display names).
    """

    name = "slack"

    def __init__(
        self,
        bot_token: str,
        channel_ids: Optional[list[str]] = None,
        channel_names: Optional[list[str]] = None,
        days_back: int = 30,
        include_threads: bool = True,
        include_bot_messages: bool = False,
        max_messages_per_channel: int = 1000,
        max_channels: int = 50,
    ) -> None:
        """
        Args:
            bot_token: Slack Bot User OAuth Token (xoxb-...).
            channel_ids: Specific channel IDs to pull from.
            channel_names: Channel names (without #) to resolve and pull from.
            days_back: Number of days of history to pull.
            include_threads: Whether to fetch full thread replies.
            include_bot_messages: Whether to include messages from bots.
            max_messages_per_channel: Max messages per channel.
            max_channels: Max number of channels if auto-discovering.
        """
        self.bot_token = bot_token
        self.channel_ids = channel_ids or []
        self.channel_names = channel_names or []
        self.days_back = days_back
        self.include_threads = include_threads
        self.include_bot_messages = include_bot_messages
        self.max_messages_per_channel = max_messages_per_channel
        self.max_channels = max_channels
        self._user_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    async def _slack_get(self, client, method: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Call a Slack Web API method (GET)."""
        resp = await client.get(
            f"{_SLACK_BASE}/{method}",
            headers=self._headers(),
            params=params or {},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            raise ConnectorError(f"Slack API error ({method}): {error}")
        return data

    async def _slack_post(self, client, method: str, json_body: Optional[dict] = None) -> dict[str, Any]:
        """Call a Slack Web API method (POST)."""
        resp = await client.post(
            f"{_SLACK_BASE}/{method}",
            headers=self._headers(),
            json=json_body or {},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            raise ConnectorError(f"Slack API error ({method}): {error}")
        return data

    async def _resolve_user(self, client, user_id: str) -> str:
        """Resolve a Slack user ID to a display name."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            data = await self._slack_get(client, "users.info", {"user": user_id})
            user = data.get("user", {})
            name = (
                user.get("profile", {}).get("display_name")
                or user.get("profile", {}).get("real_name")
                or user.get("name")
                or user_id
            )
            self._user_cache[user_id] = name
            return name
        except Exception:
            self._user_cache[user_id] = user_id
            return user_id

    async def _list_channels(self, client) -> list[dict[str, Any]]:
        """List public channels the bot has access to."""
        channels: list[dict[str, Any]] = []
        cursor: Optional[str] = None

        while len(channels) < self.max_channels:
            params: dict[str, Any] = {
                "types": "public_channel,private_channel",
                "exclude_archived": "true",
                "limit": min(200, self.max_channels - len(channels)),
            }
            if cursor:
                params["cursor"] = cursor

            data = await self._slack_get(client, "conversations.list", params)
            channels.extend(data.get("channels", []))

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return channels

    async def _resolve_channel_names(self, client) -> list[str]:
        """Resolve channel names to channel IDs."""
        if not self.channel_names:
            return []

        channels = await self._list_channels(client)
        name_to_id: dict[str, str] = {}
        for ch in channels:
            name_to_id[ch["name"]] = ch["id"]

        resolved: list[str] = []
        for name in self.channel_names:
            clean_name = name.lstrip("#")
            if clean_name in name_to_id:
                resolved.append(name_to_id[clean_name])
            else:
                logger.warning("Slack channel not found: #%s", clean_name)

        return resolved

    async def _get_channel_history(
        self, client, channel_id: str, oldest_ts: str
    ) -> list[dict[str, Any]]:
        """Fetch message history from a channel with pagination."""
        messages: list[dict[str, Any]] = []
        cursor: Optional[str] = None

        while len(messages) < self.max_messages_per_channel:
            params: dict[str, Any] = {
                "channel": channel_id,
                "oldest": oldest_ts,
                "limit": min(200, self.max_messages_per_channel - len(messages)),
                "inclusive": "true",
            }
            if cursor:
                params["cursor"] = cursor

            data = await self._slack_get(client, "conversations.history", params)
            messages.extend(data.get("messages", []))

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return messages

    async def _get_thread_replies(
        self, client, channel_id: str, thread_ts: str
    ) -> list[dict[str, Any]]:
        """Fetch all replies in a thread."""
        replies: list[dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            params: dict[str, Any] = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 200,
            }
            if cursor:
                params["cursor"] = cursor

            data = await self._slack_get(client, "conversations.replies", params)
            replies.extend(data.get("messages", []))

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return replies

    async def _format_message(self, client, msg: dict[str, Any]) -> str:
        """Format a single Slack message as readable text."""
        user_id = msg.get("user", "")
        user_name = await self._resolve_user(client, user_id) if user_id else "Unknown"

        ts = msg.get("ts", "0")
        try:
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, OSError):
            time_str = ts

        text = msg.get("text", "")

        # Handle attachments
        attachments = msg.get("attachments", [])
        attachment_texts = []
        for att in attachments:
            if att.get("text"):
                attachment_texts.append(att["text"])
            elif att.get("fallback"):
                attachment_texts.append(att["fallback"])

        parts = [f"[{time_str}] {user_name}: {text}"]
        if attachment_texts:
            parts.append("  Attachments: " + " | ".join(attachment_texts))

        return "\n".join(parts)

    async def _process_channel(
        self, client, channel_id: str, channel_name: str, oldest_ts: str
    ) -> Optional[Document]:
        """Process a single channel into a Document."""
        try:
            messages = await self._get_channel_history(client, channel_id, oldest_ts)

            if not messages:
                logger.debug("No messages in channel #%s", channel_name)
                return None

            # Filter bot messages if needed
            if not self.include_bot_messages:
                messages = [m for m in messages if not m.get("bot_id") and m.get("subtype") != "bot_message"]

            # Sort messages by timestamp (oldest first)
            messages.sort(key=lambda m: float(m.get("ts", "0")))

            formatted_parts: list[str] = []

            for msg in messages:
                formatted = await self._format_message(client, msg)
                formatted_parts.append(formatted)

                # Fetch thread replies if the message has them
                if self.include_threads and msg.get("reply_count", 0) > 0:
                    thread_ts = msg.get("ts", "")
                    replies = await self._get_thread_replies(client, channel_id, thread_ts)
                    # Skip first reply as it's the parent message
                    for reply in replies[1:]:
                        if not self.include_bot_messages and (reply.get("bot_id") or reply.get("subtype") == "bot_message"):
                            continue
                        reply_text = await self._format_message(client, reply)
                        formatted_parts.append(f"  (thread) {reply_text}")

            if not formatted_parts:
                return None

            content = "\n".join(formatted_parts)

            return Document(
                content=content,
                title=f"Slack channel: #{channel_name}",
                source=f"slack://channel/{channel_id}",
                metadata={
                    "connector": self.name,
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "message_count": len(messages),
                    "days_back": self.days_back,
                },
            )

        except Exception as exc:
            logger.warning("Failed to process channel #%s (%s): %s", channel_name, channel_id, exc)
            return None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull message history from Slack channels.

        Returns:
            List of Document instances, one per channel.

        Raises:
            ConnectorError: On authentication or API errors.
        """
        import httpx

        try:
            oldest = datetime.now(tz=timezone.utc) - timedelta(days=self.days_back)
            oldest_ts = str(oldest.timestamp())

            async with httpx.AsyncClient(timeout=60) as client:
                # Resolve target channels
                target_channel_ids = list(self.channel_ids)
                resolved = await self._resolve_channel_names(client)
                target_channel_ids.extend(resolved)

                # If no channels specified, discover them
                channel_map: dict[str, str] = {}  # id -> name
                if not target_channel_ids:
                    channels = await self._list_channels(client)
                    for ch in channels:
                        if ch.get("is_member"):
                            channel_map[ch["id"]] = ch["name"]
                else:
                    # Fetch channel info for the specified IDs
                    for cid in target_channel_ids:
                        try:
                            data = await self._slack_get(client, "conversations.info", {"channel": cid})
                            ch = data.get("channel", {})
                            channel_map[cid] = ch.get("name", cid)
                        except Exception:
                            channel_map[cid] = cid

                logger.info("Slack: processing %d channels", len(channel_map))

                documents: list[Document] = []
                for cid, cname in channel_map.items():
                    doc = await self._process_channel(client, cid, cname, oldest_ts)
                    if doc:
                        documents.append(doc)

                logger.info("Slack: extracted %d channel documents", len(documents))
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"Slack pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test the Slack API connection by calling auth.test.

        Returns:
            True if the bot token is valid.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                data = await self._slack_get(client, "auth.test")
                logger.info("Slack connected as bot: %s (team: %s)", data.get("user"), data.get("team"))
                return True
        except Exception as exc:
            raise ConnectionTestFailedError(f"Slack connection test failed: {exc}") from exc
