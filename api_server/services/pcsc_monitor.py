"""
Low-level PC/SC event monitoring utilities.

This module provides event-driven card monitoring using SCardGetStatusChange,
matching the approach used in the Go implementation for instant event detection.
"""

import logging
from typing import Optional, Tuple
from smartcard.scard import (
    SCardEstablishContext,
    SCardReleaseContext,
    SCardListReaders,
    SCardGetStatusChange,
    SCARD_SCOPE_USER,
    SCARD_STATE_UNAWARE,
    SCARD_STATE_PRESENT,
    SCARD_STATE_EMPTY,
    INFINITE,
)

logger = logging.getLogger(__name__)


class ReaderState:
    """Represents the state of a card reader."""

    def __init__(self, reader_name: str):
        self.reader_name = reader_name
        self.current_state = SCARD_STATE_UNAWARE
        self.event_state = SCARD_STATE_UNAWARE


class PCSCMonitor:
    """
    Event-driven PC/SC card monitor using SCardGetStatusChange.

    This provides blocking, hardware-level event detection similar to
    the Go implementation, eliminating the need for polling.
    """

    def __init__(self):
        """Initialize PC/SC monitor."""
        self.context = None
        self.reader_states = []

    def establish_context(self) -> int:
        """
        Establish a PC/SC context.

        Returns:
            int: The PC/SC context handle

        Raises:
            Exception: If context establishment fails
        """
        if self.context is not None:
            return self.context

        result, context = SCardEstablishContext(SCARD_SCOPE_USER)
        if result != 0:
            raise Exception(f"Failed to establish PC/SC context: {result}")

        self.context = context
        logger.debug(f"Established PC/SC context: {context}")
        return context

    def release_context(self):
        """Release the PC/SC context."""
        if self.context is not None:
            try:
                SCardReleaseContext(self.context)
                logger.debug("Released PC/SC context")
            except Exception as e:
                logger.warning(f"Error releasing PC/SC context: {e}")
            finally:
                self.context = None

    def list_readers(self) -> list[str]:
        """
        List available card readers.

        Returns:
            list[str]: List of reader names

        Raises:
            Exception: If listing readers fails
        """
        ctx = self.establish_context()
        result, readers = SCardListReaders(ctx, [])

        if result != 0:
            raise Exception(f"Failed to list readers: {result}")

        return readers if readers else []

    def init_reader_states(self, readers: list[str]) -> list:
        """
        Initialize reader states for monitoring.

        Args:
            readers: List of reader names to monitor

        Returns:
            list: Reader states in pyscard format
        """
        reader_states = []
        for reader in readers:
            reader_states.append((reader, SCARD_STATE_UNAWARE))

        self.reader_states = reader_states
        logger.debug(f"Initialized reader states for {len(readers)} readers")
        return reader_states

    def wait_for_card_present(self, timeout: int = INFINITE) -> Tuple[int, str]:
        """
        Block until a card is present in any monitored reader.

        This uses SCardGetStatusChange with infinite timeout (by default),
        providing instant hardware-level event detection without polling.

        Args:
            timeout: Timeout in milliseconds (INFINITE for blocking)

        Returns:
            Tuple[int, str]: (reader_index, reader_name) where card was detected

        Raises:
            Exception: If GetStatusChange fails or no readers are monitored
        """
        if not self.reader_states:
            raise Exception("No reader states initialized")

        ctx = self.establish_context()

        while True:
            # Block until state change occurs
            result, new_states = SCardGetStatusChange(
                ctx,
                timeout,
                self.reader_states
            )

            if result != 0:
                raise Exception(f"SCardGetStatusChange failed: {result}")

            # Update states and check for card present
            for i, (reader, event_state, atr) in enumerate(new_states):
                # Update current state for next call
                self.reader_states[i] = (reader, event_state)

                # Check if card is present
                if event_state & SCARD_STATE_PRESENT:
                    logger.info(f"Card detected in reader {i}: {reader}")
                    return i, reader

    def wait_for_card_removed(self, timeout: int = INFINITE) -> Tuple[int, str]:
        """
        Block until a card is removed from any monitored reader.

        This uses SCardGetStatusChange with infinite timeout (by default),
        providing instant hardware-level event detection without polling.

        Args:
            timeout: Timeout in milliseconds (INFINITE for blocking)

        Returns:
            Tuple[int, str]: (reader_index, reader_name) where card was removed

        Raises:
            Exception: If GetStatusChange fails or no readers are monitored
        """
        if not self.reader_states:
            raise Exception("No reader states initialized")

        ctx = self.establish_context()

        while True:
            # Block until state change occurs
            result, new_states = SCardGetStatusChange(
                ctx,
                timeout,
                self.reader_states
            )

            if result != 0:
                raise Exception(f"SCardGetStatusChange failed: {result}")

            # Update states and check for card removed
            for i, (reader, event_state, atr) in enumerate(new_states):
                # Update current state for next call
                self.reader_states[i] = (reader, event_state)

                # Check if card is empty/removed
                if event_state & SCARD_STATE_EMPTY:
                    logger.info(f"Card removed from reader {i}: {reader}")
                    return i, reader

    def __enter__(self):
        """Context manager entry."""
        self.establish_context()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release_context()
        return False
