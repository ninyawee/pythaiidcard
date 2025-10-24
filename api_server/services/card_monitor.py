"""Card monitoring service for detecting and reading Thai ID cards."""

import asyncio
import logging
import base64
from typing import Optional
from datetime import datetime

from pythaiidcard import ThaiIDCardReader
from pythaiidcard.exceptions import (
    NoReaderFoundError,
    NoCardDetectedError,
    CardConnectionError,
)
from pythaiidcard.models import ThaiIDCard

from ..models.api_models import WebSocketEvent, WebSocketEventType
from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class CardMonitorService:
    """
    Background service that monitors card readers for insertion/removal events
    and automatically reads card data when a card is detected.
    """

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize card monitor service.

        Args:
            connection_manager: The connection manager for broadcasting events
        """
        self.connection_manager = connection_manager
        self.monitoring = False
        self.last_card_data: Optional[ThaiIDCard] = None
        self.reader: Optional[ThaiIDCardReader] = None
        self.current_reader_name: Optional[str] = None
        self.card_present = False
        logger.info("Card monitor service initialized")

    async def start_monitoring(self, poll_interval: float = 1.0):
        """
        Start monitoring for card events.

        Args:
            poll_interval: Time in seconds between reader polls (default: 1.0)
        """
        self.monitoring = True
        logger.info("Card monitoring started")

        while self.monitoring:
            try:
                await self._check_readers()
            except Exception as e:
                logger.error(f"Error in card monitoring loop: {e}")
                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.ERROR,
                        message=f"Monitoring error: {str(e)}",
                        error_code="MONITORING_ERROR",
                    )
                )

            await asyncio.sleep(poll_interval)

    def stop_monitoring(self):
        """Stop the monitoring loop."""
        logger.info("Stopping card monitoring")
        self.monitoring = False
        if self.reader:
            try:
                self.reader.disconnect()
            except Exception:
                pass
            self.reader = None

    async def _check_readers(self):
        """Check for available readers and card presence."""
        try:
            # Get available readers
            readers = ThaiIDCardReader.list_readers()

            if not readers:
                # No readers detected
                if self.current_reader_name is not None:
                    # Reader was removed
                    logger.warning("No card readers detected")
                    await self.broadcast_event(
                        WebSocketEvent(
                            type=WebSocketEventType.READER_STATUS,
                            message="No card readers detected",
                            data={"status": "no_readers"},
                        )
                    )
                    self.current_reader_name = None
                    self.card_present = False
                return

            # Use first available reader
            reader_name = readers[0]

            # Check if this is a new reader
            if reader_name != self.current_reader_name:
                logger.info(f"Reader detected: {reader_name}")
                self.current_reader_name = reader_name
                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.READER_STATUS,
                        message="Card reader connected",
                        reader=reader_name,
                        data={"status": "reader_connected"},
                    )
                )

            # Try to detect card
            await self._check_card_presence(reader_name)

        except Exception as e:
            logger.error(f"Error checking readers: {e}")

    async def _check_card_presence(self, reader_name: str):
        """
        Check if a card is present and read it if newly inserted.

        Args:
            reader_name: Name of the reader to check
        """
        try:
            # Try to connect to reader
            temp_reader = ThaiIDCardReader(reader_name)
            temp_reader.connect()

            # Card is present and connected
            if not self.card_present:
                # Card was just inserted
                logger.info("Card inserted")
                self.card_present = True
                self.reader = temp_reader

                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.CARD_INSERTED,
                        message="Card detected",
                        reader=reader_name,
                    )
                )

                # Automatically read the card
                await self.read_and_broadcast(include_photo=True)
            else:
                # Card was already present, close temp connection
                temp_reader.disconnect()

        except (NoCardDetectedError, CardConnectionError):
            # No card present
            if self.card_present:
                # Card was removed
                logger.info("Card removed")
                self.card_present = False
                if self.reader:
                    try:
                        self.reader.disconnect()
                    except Exception:
                        pass
                    self.reader = None

                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.CARD_REMOVED,
                        message="Card removed",
                        reader=reader_name,
                    )
                )

        except Exception as e:
            logger.error(f"Error checking card presence: {e}")

    async def read_and_broadcast(self, include_photo: bool = True):
        """
        Read card data and broadcast to all connected clients.

        Args:
            include_photo: Whether to include photo data (default: True)
        """
        if not self.reader:
            logger.warning("Cannot read card: no reader connection")
            await self.broadcast_event(
                WebSocketEvent(
                    type=WebSocketEventType.ERROR,
                    message="No reader connection available",
                    error_code="NO_READER_CONNECTION",
                )
            )
            return

        try:
            logger.info("Reading card data...")
            # Read card data (this may take a few seconds with photo)
            card_data = await asyncio.to_thread(
                self.reader.read_card, include_photo=include_photo
            )

            self.last_card_data = card_data
            logger.info(f"Card read successful: CID {card_data.cid}")

            # Convert to dict for JSON serialization
            card_dict = card_data.model_dump()

            # Convert photo bytes to base64 if present
            if card_dict.get("photo"):
                photo_bytes = card_dict["photo"]
                card_dict["photo_base64"] = f"data:image/jpeg;base64,{base64.b64encode(photo_bytes).decode('utf-8')}"
                # Remove raw bytes from response
                del card_dict["photo"]

            await self.broadcast_event(
                WebSocketEvent(
                    type=WebSocketEventType.CARD_READ,
                    message="Card data read successfully",
                    data=card_dict,
                    reader=self.current_reader_name,
                )
            )

        except Exception as e:
            logger.error(f"Error reading card: {e}")
            await self.broadcast_event(
                WebSocketEvent(
                    type=WebSocketEventType.ERROR,
                    message=f"Failed to read card: {str(e)}",
                    error_code="CARD_READ_ERROR",
                )
            )

    async def broadcast_event(self, event: WebSocketEvent):
        """
        Broadcast an event to all connected clients.

        Args:
            event: The event to broadcast
        """
        await self.connection_manager.broadcast(event)

    def get_status(self) -> dict:
        """
        Get current monitoring status.

        Returns:
            Dictionary with current status information
        """
        return {
            "monitoring": self.monitoring,
            "reader_name": self.current_reader_name,
            "card_present": self.card_present,
            "last_read": self.last_card_data.model_dump() if self.last_card_data else None,
        }

    def get_available_readers(self) -> list[str]:
        """
        Get list of available card readers.

        Returns:
            List of reader names
        """
        try:
            return ThaiIDCardReader.list_readers()
        except Exception as e:
            logger.error(f"Error listing readers: {e}")
            return []
