"""Pydantic models for API request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class ServerStatus(BaseModel):
    """Server status response."""

    status: str = Field(description="Server status (running/stopped)")
    version: str = Field(description="API version")
    readers_available: int = Field(description="Number of card readers detected")
    card_detected: bool = Field(description="Whether a card is currently detected")
    reader_name: Optional[str] = Field(None, description="Name of active reader")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class CardReadResponse(BaseModel):
    """Response from card read operation."""

    success: bool = Field(description="Whether the read was successful")
    data: Optional[dict] = Field(None, description="Card data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Read timestamp")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(description="Error code identifier")
    message: str = Field(description="Human-readable error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class WebSocketEventType(str, Enum):
    """WebSocket event types."""

    CONNECTED = "connected"
    CARD_INSERTED = "card_inserted"
    CARD_REMOVED = "card_removed"
    CARD_READ = "card_read"
    READER_STATUS = "reader_status"
    ERROR = "error"
    PONG = "pong"


class WebSocketCommandType(str, Enum):
    """WebSocket command types from client."""

    SUBSCRIBE = "subscribe"
    READ_CARD = "read_card"
    PING = "ping"


class WebSocketMessage(BaseModel):
    """WebSocket message from client."""

    type: str = Field(description="Message type")
    data: Optional[dict] = Field(None, description="Message data payload")


class WebSocketEvent(BaseModel):
    """WebSocket event sent to client."""

    type: WebSocketEventType = Field(description="Event type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    data: Optional[Any] = Field(None, description="Event data")
    message: Optional[str] = Field(None, description="Optional message")
    reader: Optional[str] = Field(None, description="Reader name if applicable")
    error_code: Optional[str] = Field(None, description="Error code if error event")

    class Config:
        """Pydantic config."""

        use_enum_values = True
