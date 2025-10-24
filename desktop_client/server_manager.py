"""Server lifecycle management for desktop client."""

import logging
import threading
import time
from typing import Optional
import uvicorn

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages the FastAPI server lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        Initialize server manager.

        Args:
            host: Host to bind server to
            port: Port to bind server to
        """
        self.host = host
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.server: Optional[uvicorn.Server] = None
        self.running = False
        logger.info(f"Server manager initialized for {host}:{port}")

    def start(self) -> bool:
        """
        Start the FastAPI server in a background thread.

        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self.running:
            logger.warning("Server is already running")
            return False

        try:
            # Create server configuration
            config = uvicorn.Config(
                "api_server.main:app",
                host=self.host,
                port=self.port,
                log_level="info",
            )

            self.server = uvicorn.Server(config)

            # Start server in background thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="FastAPI-Server",
            )
            self.server_thread.start()

            # Wait a moment for server to start
            time.sleep(1)

            self.running = True
            logger.info(f"Server started on {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.running = False
            return False

    def _run_server(self):
        """Run the uvicorn server (called in thread)."""
        try:
            import asyncio

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run server
            loop.run_until_complete(self.server.serve())

        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False

    def stop(self) -> bool:
        """
        Stop the FastAPI server.

        Returns:
            bool: True if server stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Server is not running")
            return False

        try:
            if self.server:
                self.server.should_exit = True

            # Wait for thread to finish (with timeout)
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5.0)

            self.running = False
            self.server = None
            self.server_thread = None

            logger.info("Server stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False

    def is_running(self) -> bool:
        """
        Check if server is running.

        Returns:
            bool: True if server is running, False otherwise
        """
        return self.running and self.server_thread is not None and self.server_thread.is_alive()

    def restart(self) -> bool:
        """
        Restart the server.

        Returns:
            bool: True if restart successful, False otherwise
        """
        logger.info("Restarting server...")
        self.stop()
        time.sleep(2)
        return self.start()
