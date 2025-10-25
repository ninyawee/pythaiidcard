"""Settings management for desktop client."""

import json
import logging
import socket
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class Settings:
    """Manages application settings."""

    def __init__(self):
        """Initialize settings with defaults."""
        self.config_dir = Path.home() / ".pythaiidcard"
        self.config_file = self.config_dir / "settings.json"
        self.passcode_file = self.config_dir / "passcode.json"

        # Default settings
        self.port = 8765
        self.host = "127.0.0.1"
        self.bind_interface = "127.0.0.1"  # Network interface to bind to (localhost by default)
        self.auto_start = False
        self.notifications_enabled = True
        self.auto_copy_enabled = True

        # Passcode settings (loaded from separate file shared with API server)
        self.passcode = ""
        self.passcode_created_at = None

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load settings from file if exists
        self.load()
        self.load_passcode()

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
            self.bind_interface = data.get("bind_interface", "127.0.0.1")
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
                "bind_interface": self.bind_interface,
                "auto_start": self.auto_start,
                "notifications_enabled": self.notifications_enabled,
                "auto_copy_enabled": self.auto_copy_enabled,
            }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Settings saved to file")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def load_passcode(self):
        """Load passcode from shared passcode file."""
        if not self.passcode_file.exists():
            logger.info("No passcode file found")
            return

        try:
            with open(self.passcode_file, "r") as f:
                data = json.load(f)

            self.passcode = data.get("passcode", "")
            self.passcode_created_at = data.get("created_at")

            logger.info("Passcode loaded from file")

        except Exception as e:
            logger.error(f"Error loading passcode: {e}")

    def get_available_interfaces(self) -> List[Tuple[str, str]]:
        """
        Get list of available network interfaces.

        Returns:
            List of tuples (display_name, ip_address)
        """
        interfaces = [
            ("Localhost only (127.0.0.1)", "127.0.0.1"),
            ("All interfaces (0.0.0.0)", "0.0.0.0"),
        ]

        # Try to get local network interfaces
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip and local_ip not in ["127.0.0.1", "0.0.0.0"]:
                interfaces.append((f"Local Network ({local_ip})", local_ip))
        except Exception as e:
            logger.warning(f"Could not detect local network interface: {e}")

        return interfaces

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"

    @property
    def websocket_url(self) -> str:
        """Get the WebSocket URL."""
        return f"ws://{self.host}:{self.port}/ws"
