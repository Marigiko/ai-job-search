"""WebSocket endpoint for real-time client updates."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)

__all__ = ["manager", "broadcast", "router"]


class ConnectionManager:
    """Track active WebSocket clients and broadcast messages to them."""

    def __init__(self) -> None:
        self._active: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def connect(self, ws: WebSocket) -> AsyncIterator[None]:
        await ws.accept()
        async with self._lock:
            self._active.add(ws)
        logger.info("WebSocket client connected (total=%d)", len(self._active))
        try:
            yield
        finally:
            async with self._lock:
                self._active.discard(ws)
            logger.info("WebSocket client disconnected (total=%d)", len(self._active))

    async def broadcast(self, message: dict[str, Any]) -> int:
        """Send a message to every connected client. Returns delivery count."""
        disconnected: list[WebSocket] = []
        delivered = 0
        for ws in self._active:
            try:
                await ws.send_json(message)
                delivered += 1
            except RuntimeError:
                disconnected.append(ws)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self._active.discard(ws)

        return delivered

    @property
    def active_count(self) -> int:
        return len(self._active)


manager = ConnectionManager()


async def broadcast(message: dict[str, Any]) -> int:
    """Convenience wrapper around ``manager.broadcast`` for service modules."""
    return await manager.broadcast(message)


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Accept a WebSocket, echo messages back until disconnect."""
    async with manager.connect(ws):
        try:
            while True:
                data = await ws.receive_text()
                await ws.send_json({"type": "echo", "payload": data})
        except WebSocketDisconnect:
            pass
