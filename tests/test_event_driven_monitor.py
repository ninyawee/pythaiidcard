#!/usr/bin/env python3
"""
Test script for event-driven card monitoring.

This script demonstrates the improved event-driven card monitoring
that matches the Go implementation's continuous event emission.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Setup path for imports
sys.path.insert(0, '.')

from api_server.services.pcsc_monitor import PCSCMonitor
from api_server.services.card_monitor import CardMonitorService
from api_server.services.connection_manager import ConnectionManager

# Configure logging to show timestamps and event details
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


async def test_event_driven_monitoring():
    """
    Test the event-driven monitoring system.

    This will:
    1. Wait for a card reader
    2. Detect card insertion instantly (no polling delay)
    3. Emit card_inserted event
    4. Wait for card removal instantly (no polling delay)
    5. Emit card_removed event
    6. Loop continuously
    """
    logger.info("=" * 80)
    logger.info("Event-Driven Card Monitor Test (v2.3.0)")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This test demonstrates instant hardware-level event detection")
    logger.info("using SCardGetStatusChange (matching Go implementation).")
    logger.info("")
    logger.info("Please insert and remove your Thai ID card to test...")
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 80)
    logger.info("")

    # Create connection manager and card monitor
    connection_manager = ConnectionManager()
    card_monitor = CardMonitorService(
        connection_manager,
        auto_read_on_insert=False  # On-demand mode for testing
    )

    # Start monitoring (this runs continuously)
    try:
        await card_monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 80)
        logger.info("Test interrupted by user")
        logger.info("=" * 80)
        card_monitor.stop_monitoring()


async def test_low_level_pcsc():
    """
    Test low-level PC/SC event detection directly.

    This demonstrates the blocking behavior of SCardGetStatusChange.
    """
    logger.info("=" * 80)
    logger.info("Low-Level PC/SC Monitor Test")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Testing direct SCardGetStatusChange blocking behavior...")
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 80)
    logger.info("")

    with PCSCMonitor() as monitor:
        # List readers
        readers = monitor.list_readers()
        logger.info(f"Found {len(readers)} reader(s): {readers}")

        if not readers:
            logger.error("No card readers found!")
            return

        # Initialize reader states
        monitor.init_reader_states(readers)
        logger.info("Initialized reader states for monitoring")
        logger.info("")

        try:
            iteration = 1
            while True:
                # Wait for card present (this blocks with NO polling)
                logger.info(f"[Iteration {iteration}] Waiting for card insertion (blocking)...")
                start_time = datetime.now()

                reader_index, reader_name = await asyncio.to_thread(
                    monitor.wait_for_card_present
                )

                insert_latency = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"✓ Card inserted in {reader_name} (latency: {insert_latency:.1f}ms)")

                # Wait for card removed (this blocks with NO polling)
                logger.info(f"[Iteration {iteration}] Waiting for card removal (blocking)...")
                start_time = datetime.now()

                reader_index, reader_name = await asyncio.to_thread(
                    monitor.wait_for_card_removed
                )

                remove_latency = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"✓ Card removed from {reader_name} (latency: {remove_latency:.1f}ms)")
                logger.info("")

                iteration += 1

        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 80)
            logger.info("Test interrupted by user")
            logger.info(f"Completed {iteration - 1} insert/remove cycles")
            logger.info("=" * 80)


async def main():
    """Main test runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--low-level":
        await test_low_level_pcsc()
    else:
        await test_event_driven_monitoring()


if __name__ == "__main__":
    print()
    print("Event-Driven Card Monitor Test Suite")
    print("=====================================")
    print()
    print("Usage:")
    print("  python test_event_driven_monitor.py              # Test full monitoring service")
    print("  python test_event_driven_monitor.py --low-level  # Test low-level PC/SC only")
    print()

    asyncio.run(main())
