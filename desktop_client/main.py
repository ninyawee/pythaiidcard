"""Main entry point for desktop client."""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pythaiidcard-desktop.log"),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for desktop application."""
    try:
        logger.info("=" * 60)
        logger.info("Thai ID Card Reader - Desktop Client")
        logger.info("=" * 60)

        from .tray_app import TrayApp

        # Create and run tray application
        app = TrayApp()
        app.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
