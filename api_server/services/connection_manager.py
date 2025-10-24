"""WebSocket connection manager for handling multiple client connections."""

import logging
from typing import List
from fastapi import WebSocket

from ..models.api_models import WebSocketEvent

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to connected clients."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []
        logger.info("Connection manager initialized")

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_event(self, websocket: WebSocket, event: WebSocketEvent):
        """
        Send an event to a specific WebSocket connection.

        Args:
            websocket: The target WebSocket connection
            event: The event to send
        """
        try:
            await websocket.send_json(event.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Error sending event to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, event: WebSocketEvent):
        """
        Broadcast an event to all connected clients.

        Args:
            event: The event to broadcast

        Disconnects any clients that fail to receive the message.
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        disconnected = []
        event_dict = event.model_dump(mode="json")

        logger.debug(f"Broadcasting {event.type} event to {len(self.active_connections)} clients")

        for connection in self.active_connections:
            try:
                await connection.send_json(event_dict)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up failed connections
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_dict(self, data: dict):
        """
        Broadcast a dictionary to all connected clients (convenience method).

        Args:
            data: Dictionary to broadcast
        """
        if not self.active_connections:
            return

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting dict to connection: {e}")
                disconnected.append(connection)

        # Clean up failed connections
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
