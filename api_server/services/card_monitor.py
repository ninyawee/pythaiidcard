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
    DataReadError,
    CommandError,
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

    VERSION = "2.2.0"

    def __init__(self, connection_manager: ConnectionManager, auto_read_on_insert: bool = False):
        """
        Initialize card monitor service.

        Args:
            connection_manager: The connection manager for broadcasting events
            auto_read_on_insert: Whether to automatically read card on insertion (default: False)
                                 Set to False for readers with hardware limitations (e.g., Alcor Link AK9563)
        """
        self.connection_manager = connection_manager
        self.monitoring = False
        self.last_card_data: Optional[ThaiIDCard] = None
        self.reader: Optional[ThaiIDCardReader] = None
        self.current_reader_name: Optional[str] = None
        self.card_present = False
        self.auto_read_on_insert = auto_read_on_insert  # v2.2.0: On-demand mode by default
        # Caching fields (v2.1.0)
        self.cache_valid = False  # True if cached data is fresh for current insertion
        self.last_read_timestamp: Optional[datetime] = None  # When card was last read
        logger.info(
            f"Card monitor service initialized (version {self.VERSION}, "
            f"auto-read: {'enabled' if auto_read_on_insert else 'disabled - on-demand mode'})"
        )

    async def start_monitoring(self, poll_interval: float = 1.0):
        """
        Start monitoring for card events.

        Args:
            poll_interval: Time in seconds between reader polls (default: 1.0)
        """
        self.monitoring = True
        logger.info(f"Card monitoring started (version {self.VERSION})")

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

            # Adaptive polling: check less frequently when card is already present
            # to reduce log spam and CPU usage
            if self.card_present and self.reader:
                # Card is present and connected - check every 5 seconds for removal
                await asyncio.sleep(poll_interval * 5)
            else:
                # No card - check every second for insertion
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

            # Use first available reader (extract name from CardReaderInfo)
            reader_info = readers[0]
            reader_name = reader_info.name

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
        # If card is already present, skip checking (avoid connect/disconnect spam)
        # The existing connection will be used for reads, and removal will be detected
        # via exceptions during read operations
        if self.card_present and self.reader:
            # Card is already known to be present, no need to reconnect
            return

        try:
            # Try to connect to reader using index 0 (first reader)
            temp_reader = ThaiIDCardReader(reader_index=0)
            temp_reader.connect()

            # Card is present and connected (this is a new insertion)
            logger.info("Card inserted")
            self.card_present = True
            self.reader = temp_reader

            await self.broadcast_event(
                WebSocketEvent(
                    type=WebSocketEventType.CARD_INSERTED,
                    message="Card detected - ready for reading" if not self.auto_read_on_insert else "Card detected - reading automatically...",
                    reader=reader_name,
                )
            )

            # Automatically read the card with photo (if enabled)
            # v2.2.0: Default is on-demand mode due to hardware limitations with some readers
            # (e.g., Alcor Link AK9563 cannot reliably auto-read on insertion)
            if self.auto_read_on_insert:
                logger.info("Auto-read enabled - reading card data with photo...")
                await self.read_and_broadcast(include_photo=True)
            else:
                logger.info("On-demand mode - waiting for manual read request")

        except (NoCardDetectedError, CardConnectionError):
            # No card present
            if self.card_present:
                # Card was removed
                logger.info("Card removed - invalidating cache")
                self.card_present = False
                self.cache_valid = False  # Invalidate cache on card removal
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
        Serves cached data instantly if card is still present from previous read.

        Args:
            include_photo: Whether to include photo data (default: True)
        """
        # Check if cache is valid for current card insertion
        if self.cache_valid and self.last_card_data:
            logger.info("Serving cached card data (card still present since last read)")
            card_dict = self.last_card_data.model_dump()

            # Convert photo bytes to base64 if present
            if card_dict.get("photo"):
                photo_bytes = card_dict["photo"]
                card_dict["photo_base64"] = f"data:image/jpeg;base64,{base64.b64encode(photo_bytes).decode('utf-8')}"
                del card_dict["photo"]

            await self.broadcast_event(
                WebSocketEvent(
                    type=WebSocketEventType.CARD_READ,
                    message="Card data from cache (remove card for fresh read)",
                    data={
                        **card_dict,
                        "cached": True,
                        "read_at": self.last_read_timestamp.isoformat() if self.last_read_timestamp else None,
                    },
                    reader=self.current_reader_name,
                )
            )
            return

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
            logger.info("Reading card data from hardware...")
            # Read card data (this may take a few seconds with photo)
            card_data = await asyncio.to_thread(
                self.reader.read_card, include_photo=include_photo
            )

            # Update cache
            self.last_card_data = card_data
            self.cache_valid = True  # Mark cache as valid for this insertion
            self.last_read_timestamp = datetime.now()
            logger.info(f"Card read successful: CID {card_data.cid} (cached for future reads)")

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
                    data={
                        **card_dict,
                        "cached": False,
                        "read_at": self.last_read_timestamp.isoformat(),
                    },
                    reader=self.current_reader_name,
                )
            )

        except (NoCardDetectedError, CardConnectionError, DataReadError, CommandError) as e:
            # Card connection was lost - likely a "card reset" error
            # Try to reconnect immediately rather than waiting for monitoring loop
            error_msg = str(e)
            logger.warning(f"Card connection lost during read: {error_msg}")

            # Close the stale connection
            if self.reader:
                try:
                    self.reader.disconnect()
                except Exception:
                    pass
                self.reader = None

            # Try to reconnect immediately (common after card reset errors)
            logger.info("Attempting immediate reconnection...")
            try:
                # Wait a brief moment for hardware to stabilize after reset
                await asyncio.sleep(0.2)

                new_reader = ThaiIDCardReader(reader_index=0)
                new_reader.connect()
                self.reader = new_reader
                self.card_present = True

                # Wait another brief moment after connection for hardware to be ready
                await asyncio.sleep(0.1)

                logger.info("Reconnected successfully - ready for next read")

                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.READER_STATUS,
                        message="Connection reset - reconnected automatically",
                        data={"status": "reconnected"},
                    )
                )
            except Exception as reconnect_error:
                # Reconnection failed - card might actually be removed
                logger.warning(f"Reconnection failed: {reconnect_error}")
                self.card_present = False
                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.CARD_REMOVED,
                        message="Card removed or not responding",
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
            readers = ThaiIDCardReader.list_readers()
            return [reader.name for reader in readers]
        except Exception as e:
            logger.error(f"Error listing readers: {e}")
            return []

    def clear_cache(self) -> bool:
        """
        Manually clear the cached card data.

        Returns:
            True if cache was cleared, False if no cache existed
        """
        if self.cache_valid or self.last_card_data:
            logger.info("Cache cleared manually")
            self.cache_valid = False
            self.last_card_data = None
            self.last_read_timestamp = None
            return True
        return False
