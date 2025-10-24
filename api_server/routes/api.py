"""REST API routes for Thai ID Card Reader server."""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from pythaiidcard import ThaiIDCardReader
from ..models.api_models import (
    ServerStatus,
    CardReadResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

# This will be set by the main application
_card_monitor = None


def get_card_monitor():
    """Dependency to get the card monitor service."""
    if _card_monitor is None:
        raise HTTPException(status_code=500, detail="Card monitor service not initialized")
    return _card_monitor


def set_card_monitor(monitor):
    """Set the card monitor service (called from main app)."""
    global _card_monitor
    _card_monitor = monitor


@router.get("/status", response_model=ServerStatus)
async def get_status(monitor=Depends(get_card_monitor)):
    """
    Get server and reader status.

    Returns:
        ServerStatus: Current server status including reader and card detection info
    """
    try:
        readers_info = ThaiIDCardReader.list_readers()
        monitor_status = monitor.get_status()

        return ServerStatus(
            status="running",
            version="2.2.0",
            readers_available=len(readers_info),
            card_detected=monitor_status["card_present"],
            reader_name=monitor_status["reader_name"],
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/readers")
async def list_readers():
    """
    List all available card readers.

    Returns:
        dict: List of available reader info
    """
    try:
        readers_info = ThaiIDCardReader.list_readers()
        # Convert CardReaderInfo objects to dicts
        readers_list = [reader.model_dump() for reader in readers_info]
        return {
            "readers": readers_list,
            "count": len(readers_list),
            "timestamp": datetime.now(),
        }
    except Exception as e:
        logger.error(f"Error listing readers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/card/current", response_model=CardReadResponse)
async def get_current_card(monitor=Depends(get_card_monitor)):
    """
    Get the last read card data (cached).

    Returns:
        CardReadResponse: Last card data if available
    """
    try:
        status = monitor.get_status()
        last_read = status.get("last_read")

        if last_read:
            # Remove photo bytes if present (too large for REST)
            if "photo" in last_read:
                del last_read["photo"]

            return CardReadResponse(
                success=True,
                data=last_read,
                timestamp=datetime.now(),
            )
        else:
            return CardReadResponse(
                success=False,
                error="No card data available",
                timestamp=datetime.now(),
            )
    except Exception as e:
        logger.error(f"Error getting current card: {e}")
        return CardReadResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now(),
        )


@router.post("/card/read", response_model=CardReadResponse)
async def read_card(
    include_photo: bool = True,
    monitor=Depends(get_card_monitor),
):
    """
    Trigger a manual card read.

    Args:
        include_photo: Whether to include photo data (default: True)

    Returns:
        CardReadResponse: Result of the read operation
    """
    try:
        # Check if card is present
        status = monitor.get_status()
        if not status["card_present"]:
            return CardReadResponse(
                success=False,
                error="No card detected in reader",
                timestamp=datetime.now(),
            )

        # Trigger read (this will broadcast to WebSocket clients)
        await monitor.read_and_broadcast(include_photo=include_photo)

        # Return the data
        last_read = monitor.get_status().get("last_read")

        if last_read:
            # Remove photo bytes for REST response
            if "photo" in last_read:
                del last_read["photo"]

            return CardReadResponse(
                success=True,
                data=last_read,
                timestamp=datetime.now(),
            )
        else:
            return CardReadResponse(
                success=False,
                error="Card read failed",
                timestamp=datetime.now(),
            )

    except Exception as e:
        logger.error(f"Error reading card: {e}")
        return CardReadResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now(),
        )


@router.post("/card/cache/clear")
async def clear_cache(monitor=Depends(get_card_monitor)):
    """
    Clear the cached card data.

    This forces the next read to fetch fresh data from the card hardware.

    Returns:
        dict: Result of the cache clear operation
    """
    try:
        cleared = monitor.clear_cache()

        return {
            "success": True,
            "cleared": cleared,
            "message": "Cache cleared successfully" if cleared else "No cache to clear",
            "timestamp": datetime.now(),
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
    }
