"""Authentication module for Chrome extension and desktop client integration."""

import json
import logging
import secrets
import string
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class PasscodeManager:
    """Manages passcode generation, storage, and validation for extension authentication."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize passcode manager.

        Args:
            config_dir: Directory to store passcode file. Defaults to ~/.pythaiidcard
        """
        if config_dir is None:
            config_dir = Path.home() / ".pythaiidcard"

        self.config_dir = config_dir
        self.passcode_file = config_dir / "passcode.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Passcode manager initialized with config dir: {self.config_dir}")

    def generate_passcode(self, length: int = 10) -> str:
        """
        Generate a cryptographically secure random passcode.

        Args:
            length: Length of passcode (default: 10)

        Returns:
            Random alphanumeric passcode
        """
        # Use uppercase, lowercase, and digits for passcode
        alphabet = string.ascii_letters + string.digits
        passcode = "".join(secrets.choice(alphabet) for _ in range(length))

        logger.info(f"Generated new {length}-character passcode")
        return passcode

    def save_passcode(self, passcode: str) -> Dict[str, str]:
        """
        Save passcode to file with timestamp.

        Args:
            passcode: The passcode to save

        Returns:
            Dictionary containing passcode and created_at timestamp
        """
        created_at = datetime.utcnow().isoformat() + "Z"

        data = {
            "passcode": passcode,
            "created_at": created_at,
        }

        try:
            with open(self.passcode_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Passcode saved to {self.passcode_file}")
            return data

        except Exception as e:
            logger.error(f"Error saving passcode: {e}")
            raise

    def load_passcode(self) -> Optional[Dict[str, str]]:
        """
        Load passcode from file.

        Returns:
            Dictionary containing passcode and created_at, or None if not found
        """
        if not self.passcode_file.exists():
            logger.warning("Passcode file not found")
            return None

        try:
            with open(self.passcode_file, "r") as f:
                data = json.load(f)

            if "passcode" not in data:
                logger.error("Invalid passcode file format: missing 'passcode' field")
                return None

            logger.info("Passcode loaded from file")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding passcode JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading passcode: {e}")
            return None

    def validate_passcode(self, provided_passcode: str) -> bool:
        """
        Validate a provided passcode against the stored passcode.

        Args:
            provided_passcode: The passcode to validate

        Returns:
            True if passcode is valid, False otherwise
        """
        stored_data = self.load_passcode()

        if stored_data is None:
            logger.warning("No passcode configured - validation failed")
            return False

        stored_passcode = stored_data.get("passcode")
        if stored_passcode is None:
            logger.error("Invalid passcode data - missing passcode field")
            return False

        # Use secrets.compare_digest for timing-attack resistant comparison
        is_valid = secrets.compare_digest(provided_passcode, stored_passcode)

        if is_valid:
            logger.info("Passcode validation successful")
        else:
            logger.warning("Passcode validation failed - incorrect passcode")

        return is_valid

    def regenerate_passcode(self, length: int = 10) -> Dict[str, str]:
        """
        Generate and save a new passcode.

        Args:
            length: Length of passcode (default: 10)

        Returns:
            Dictionary containing new passcode and created_at timestamp
        """
        passcode = self.generate_passcode(length)
        return self.save_passcode(passcode)

    def get_current_passcode(self) -> Optional[str]:
        """
        Get the current passcode without the timestamp.

        Returns:
            Current passcode string, or None if not configured
        """
        data = self.load_passcode()
        return data.get("passcode") if data else None

    def delete_passcode(self) -> bool:
        """
        Delete the passcode file.

        Returns:
            True if deleted, False if file didn't exist
        """
        if self.passcode_file.exists():
            try:
                self.passcode_file.unlink()
                logger.info("Passcode file deleted")
                return True
            except Exception as e:
                logger.error(f"Error deleting passcode file: {e}")
                raise

        logger.warning("Passcode file doesn't exist - nothing to delete")
        return False


# Global passcode manager instance
_passcode_manager: Optional[PasscodeManager] = None


def get_passcode_manager() -> PasscodeManager:
    """
    Get the global passcode manager instance.

    Returns:
        PasscodeManager instance
    """
    global _passcode_manager

    if _passcode_manager is None:
        _passcode_manager = PasscodeManager()

    return _passcode_manager


def init_passcode_manager(config_dir: Optional[Path] = None) -> PasscodeManager:
    """
    Initialize the global passcode manager with a custom config directory.

    Args:
        config_dir: Custom config directory path

    Returns:
        PasscodeManager instance
    """
    global _passcode_manager
    _passcode_manager = PasscodeManager(config_dir)
    return _passcode_manager
