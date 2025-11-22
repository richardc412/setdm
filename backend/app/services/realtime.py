"""Realtime WebSocket utilities for broadcasting message events."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.db.models import MessageModel

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts events."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket connected (%s active)", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        if websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception:
                # Ignore failures during cleanup
                pass
        logger.info("WebSocket disconnected (%s active)", len(self._connections))

    async def _snapshot(self) -> Set[WebSocket]:
        """Return a snapshot of current connections."""
        async with self._lock:
            return set(self._connections)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a JSON message to all active connections."""
        connections = await self._snapshot()
        if not connections:
            return

        stale: Set[WebSocket] = set()
        for connection in connections:
            if connection.application_state != WebSocketState.CONNECTED:
                stale.add(connection)
                continue
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("WebSocket send failed: %s", exc)
                stale.add(connection)

        for connection in stale:
            await self.disconnect(connection)


manager = ConnectionManager()


def serialize_message(message: MessageModel) -> Dict[str, Any]:
    """Serialize MessageModel into a frontend-friendly dict."""
    return {
        "object": "Message",
        "id": message.id,
        "account_id": message.account_id,
        "chat_id": message.chat_id,
        "chat_provider_id": message.chat_provider_id,
        "provider_id": message.provider_id,
        "sender_id": message.sender_id,
        "sender_attendee_id": message.sender_attendee_id,
        "text": message.text,
        "timestamp": message.timestamp,
        "is_sender": message.is_sender,
        "attachments": message.attachments or [],
        "reactions": message.reactions or [],
        "seen": message.seen,
        "seen_by": message.seen_by or {},
        "hidden": message.hidden,
        "deleted": message.deleted,
        "edited": message.edited,
        "is_event": message.is_event,
        "delivered": message.delivered,
        "sent_by_autopilot": message.sent_by_autopilot,
        "behavior": message.behavior,
        "original": message.original,
        "quoted": message.quoted,
        "reply_to": message.reply_to,
        "event_type": message.event_type,
        "replies": message.replies,
        "reply_by": message.reply_by,
        "parent": message.parent,
        "subject": message.subject,
        "message_type": message.message_type,
        "attendee_type": message.attendee_type,
        "attendee_distance": message.attendee_distance,
        "sender_urn": message.sender_urn,
        "created_at": message.created_at.isoformat(),
    }


def build_message_event(message: MessageModel) -> Dict[str, Any]:
    """Convert a MessageModel into a websocket event envelope."""
    return {
        "type": "message:new",
        "payload": serialize_message(message),
    }


async def broadcast_new_message(message: MessageModel) -> None:
    """Send a `message:new` event to all connected clients."""
    event = build_message_event(message)
    await manager.broadcast(event)


