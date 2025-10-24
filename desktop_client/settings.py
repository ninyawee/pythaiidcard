"""Settings management for desktop client."""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings."""

    def __init__(self):
        """Initialize settings with defaults."""
        self.config_dir = Path.home() / ".pythaiidcard"
        self.config_file = self.config_dir / "settings.json"

        # Default settings
        self.port = 8765
        self.host = "127.0.0.1"
        self.auto_start = False
        self.notifications_enabled = True
        self.auto_copy_enabled = True

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load settings from file if exists
        self.load()

    def load(self):
        """Load settings from file."""
        if not self.config_file.exists():
            logger.info("No settings file found, using defaults")
            return

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            self.port = data.get("port", 8765)
            self.host = data.get("host", "127.0.0.1")
            self.auto_start = data.get("auto_start", False)
            self.notifications_enabled = data.get("notifications_enabled", True)
            self.auto_copy_enabled = data.get("auto_copy_enabled", True)

            logger.info("Settings loaded from file")

        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save(self):
        """Save settings to file."""
        try:
            data = {
                "port": self.port,
                "host": self.host,
                "auto_start": self.auto_start,
                "notifications_enabled": self.notifications_enabled,
                "auto_copy_enabled": self.auto_copy_enabled,
            }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Settings saved to file")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"

    @property
    def websocket_url(self) -> str:
        """Get the WebSocket URL."""
        return f"ws://{self.host}:{self.port}/ws"
