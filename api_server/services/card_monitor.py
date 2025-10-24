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
from .pcsc_monitor import PCSCMonitor

logger = logging.getLogger(__name__)


class CardMonitorService:
    """
    Background service that monitors card readers for insertion/removal events
    and automatically reads card data when a card is detected.
    """

    VERSION = "2.3.0"

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

    async def _wait_for_readers_available(self, pcsc_monitor: PCSCMonitor) -> list[str]:
        """
        Wait for card readers to become available.

        This method blocks until at least one reader is detected.

        Args:
            pcsc_monitor: The PC/SC monitor instance

        Returns:
            list[str]: List of available reader names
        """
        while self.monitoring:
            try:
                readers = await asyncio.to_thread(pcsc_monitor.list_readers)

                if readers and len(readers) > 0:
                    logger.info(f"Found {len(readers)} reader(s): {readers}")
                    return readers

                logger.warning("No readers found, waiting 2 seconds...")
                await self.broadcast_event(
                    WebSocketEvent(
                        type=WebSocketEventType.READER_STATUS,
                        message="No card readers detected - waiting...",
                        data={"status": "no_readers"},
                    )
                )
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error listing readers: {e}")
                await asyncio.sleep(2)

        return []

    async def _wait_for_card_present(self, pcsc_monitor: PCSCMonitor) -> Optional[str]:
        """
        Wait for a card to be inserted (event-driven, no polling).

        Uses SCardGetStatusChange with infinite timeout to block until
        a card is physically inserted into any monitored reader.

        Args:
            pcsc_monitor: The PC/SC monitor instance

        Returns:
            Optional[str]: Reader name where card was detected, or None if monitoring stopped
        """
        try:
            # This blocks until a card is inserted (hardware-level event)
            reader_index, reader_name = await asyncio.to_thread(
                pcsc_monitor.wait_for_card_present
            )
            logger.info(f"Card insertion detected in reader: {reader_name}")
            return reader_name

        except Exception as e:
            logger.error(f"Error waiting for card present: {e}")
            return None

    async def _wait_for_card_removed(self, pcsc_monitor: PCSCMonitor) -> Optional[str]:
        """
        Wait for a card to be removed (event-driven, no polling).

        Uses SCardGetStatusChange with infinite timeout to block until
        a card is physically removed from any monitored reader.

        Args:
            pcsc_monitor: The PC/SC monitor instance

        Returns:
            Optional[str]: Reader name where card was removed, or None if monitoring stopped
        """
        try:
            # This blocks until a card is removed (hardware-level event)
            reader_index, reader_name = await asyncio.to_thread(
                pcsc_monitor.wait_for_card_removed
            )
            logger.info(f"Card removal detected from reader: {reader_name}")
            return reader_name

        except Exception as e:
            logger.error(f"Error waiting for card removed: {e}")
            return None

    async def start_monitoring(self, poll_interval: float = 1.0):
        """
        Start monitoring for card events using event-driven detection.

        This method uses SCardGetStatusChange for blocking, hardware-level
        event detection. No polling is performed - the monitor waits for
        actual hardware events (card insertion/removal).

        Args:
            poll_interval: Deprecated - kept for API compatibility but not used
        """
        self.monitoring = True
        logger.info(f"Card monitoring started (version {self.VERSION}, event-driven mode)")

        # Create PC/SC monitor for event-driven detection
        pcsc_monitor = PCSCMonitor()

        try:
            # Establish PC/SC context
            await asyncio.to_thread(pcsc_monitor.establish_context)

            # Event-driven state machine loop (matches Go implementation)
            while self.monitoring:
                try:
                    # Step 1: Wait for readers to be available
                    readers = await self._wait_for_readers_available(pcsc_monitor)
                    if not readers or not self.monitoring:
                        continue

                    # Initialize reader states for monitoring
                    await asyncio.to_thread(pcsc_monitor.init_reader_states, readers)

                    # Update current reader name
                    reader_name = readers[0]
                    if reader_name != self.current_reader_name:
                        self.current_reader_name = reader_name
                        await self.broadcast_event(
                            WebSocketEvent(
                                type=WebSocketEventType.READER_STATUS,
                                message="Card reader connected",
                                reader=reader_name,
                                data={"status": "reader_connected"},
                            )
                        )

                    # Step 2: Wait for card inserted (blocks until hardware event)
                    logger.info("Waiting for card insertion...")
                    reader_name = await self._wait_for_card_present(pcsc_monitor)

                    if not reader_name or not self.monitoring:
                        continue

                    # Card detected
                    self.card_present = True
                    await self.broadcast_event(
                        WebSocketEvent(
                            type=WebSocketEventType.CARD_INSERTED,
                            message="Card detected - ready for reading" if not self.auto_read_on_insert else "Card detected - reading automatically...",
                            reader=reader_name,
                        )
                    )

                    # Try to connect to the card
                    try:
                        self.reader = ThaiIDCardReader(reader_index=0)
                        self.reader.connect()
                        logger.info("Connected to card successfully")

                        # Step 3: Auto-read if enabled (v2.3.0: on-demand by default)
                        if self.auto_read_on_insert:
                            logger.info("Auto-read enabled - reading card data...")
                            await self.read_and_broadcast(include_photo=True)
                        else:
                            logger.info("On-demand mode - waiting for manual read request")

                    except Exception as e:
                        logger.error(f"Error connecting to card: {e}")
                        await self.broadcast_event(
                            WebSocketEvent(
                                type=WebSocketEventType.ERROR,
                                message=f"Failed to connect to card: {str(e)}",
                                error_code="CARD_CONNECTION_ERROR",
                            )
                        )

                    # Step 4: Wait for card removed (blocks until hardware event)
                    logger.info("Waiting for card removal...")
                    reader_name = await self._wait_for_card_removed(pcsc_monitor)

                    if not self.monitoring:
                        break

                    # Card removed
                    logger.info("Card removed - invalidating cache")
                    self.card_present = False
                    self.cache_valid = False

                    # Disconnect reader
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
                            reader=reader_name or self.current_reader_name,
                        )
                    )

                    # Loop continues - wait for next card insertion

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await self.broadcast_event(
                        WebSocketEvent(
                            type=WebSocketEventType.ERROR,
                            message=f"Monitoring error: {str(e)}",
                            error_code="MONITORING_ERROR",
                        )
                    )
                    # Wait a bit before retrying on error
                    await asyncio.sleep(2)

        finally:
            # Clean up PC/SC context
            logger.info("Releasing PC/SC context")
            await asyncio.to_thread(pcsc_monitor.release_context)

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
