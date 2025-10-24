"""System tray application for Thai ID Card Reader."""

import sys
import logging
import webbrowser
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer

from .settings import Settings
from .server_manager import ServerManager

logger = logging.getLogger(__name__)


class TrayApp:
    """System tray application for controlling the card reader server."""

    def __init__(self):
        """Initialize the tray application."""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Load settings
        self.settings = Settings()

        # Initialize server manager
        self.server_manager = ServerManager(
            host=self.settings.host,
            port=self.settings.port,
        )

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray_icon()

        # Create context menu
        self.menu = QMenu()
        self.setup_menu()

        # Set menu to tray icon
        self.tray_icon.setContextMenu(self.menu)

        # Show tray icon
        self.tray_icon.show()

        # Auto-start server if enabled
        if self.settings.auto_start:
            self.start_server()

        # Setup status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

        logger.info("Tray application initialized")

    def setup_tray_icon(self):
        """Set up the system tray icon."""
        # Use a standard icon (we'll use a simple circle for now)
        # In production, you'd use custom icon files
        icon = self.app.style().standardIcon(
            self.app.style().StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Thai ID Card Reader")

        # Double-click action - open web interface
        self.tray_icon.activated.connect(self.on_tray_activated)

    def setup_menu(self):
        """Set up the context menu."""
        # Server status (read-only)
        self.status_action = QAction("Server: Stopped", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        # Start/Stop server
        self.toggle_action = QAction("Start Server", self.menu)
        self.toggle_action.triggered.connect(self.toggle_server)
        self.menu.addAction(self.toggle_action)

        # Restart server
        self.restart_action = QAction("Restart Server", self.menu)
        self.restart_action.triggered.connect(self.restart_server)
        self.restart_action.setEnabled(False)
        self.menu.addAction(self.restart_action)

        self.menu.addSeparator()

        # Open web interface
        open_web_action = QAction("Open Web Interface", self.menu)
        open_web_action.triggered.connect(self.open_web_interface)
        self.menu.addAction(open_web_action)

        # Open API docs
        open_docs_action = QAction("Open API Docs", self.menu)
        open_docs_action.triggered.connect(self.open_api_docs)
        self.menu.addAction(open_docs_action)

        self.menu.addSeparator()

        # Settings (placeholder for now)
        # settings_action = QAction("Settings...", self.menu)
        # settings_action.triggered.connect(self.show_settings)
        # self.menu.addAction(settings_action)

        # About
        about_action = QAction("About", self.menu)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        self.menu.addSeparator()

        # Exit
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.quit_application)
        self.menu.addAction(exit_action)

    def on_tray_activated(self, reason):
        """
        Handle tray icon activation.

        Args:
            reason: Activation reason (click, double-click, etc.)
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_web_interface()

    def toggle_server(self):
        """Toggle server on/off."""
        if self.server_manager.is_running():
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """Start the server."""
        logger.info("Starting server...")
        success = self.server_manager.start()

        if success:
            self.show_notification(
                "Server Started",
                f"Card reader server is running on port {self.settings.port}",
                QSystemTrayIcon.MessageIcon.Information,
            )
            self.update_status()
        else:
            self.show_notification(
                "Server Error",
                "Failed to start card reader server",
                QSystemTrayIcon.MessageIcon.Critical,
            )

    def stop_server(self):
        """Stop the server."""
        logger.info("Stopping server...")
        success = self.server_manager.stop()

        if success:
            self.show_notification(
                "Server Stopped",
                "Card reader server has been stopped",
                QSystemTrayIcon.MessageIcon.Information,
            )
            self.update_status()
        else:
            self.show_notification(
                "Server Error",
                "Failed to stop card reader server",
                QSystemTrayIcon.MessageIcon.Warning,
            )

    def restart_server(self):
        """Restart the server."""
        logger.info("Restarting server...")
        success = self.server_manager.restart()

        if success:
            self.show_notification(
                "Server Restarted",
                "Card reader server has been restarted",
                QSystemTrayIcon.MessageIcon.Information,
            )
            self.update_status()
        else:
            self.show_notification(
                "Server Error",
                "Failed to restart card reader server",
                QSystemTrayIcon.MessageIcon.Critical,
            )

    def update_status(self):
        """Update the status display in menu."""
        if self.server_manager.is_running():
            self.status_action.setText(f"Server: Running (:{self.settings.port})")
            self.toggle_action.setText("Stop Server")
            self.restart_action.setEnabled(True)

            # Update icon tooltip
            self.tray_icon.setToolTip(
                f"Thai ID Card Reader\nServer running on port {self.settings.port}"
            )
        else:
            self.status_action.setText("Server: Stopped")
            self.toggle_action.setText("Start Server")
            self.restart_action.setEnabled(False)

            # Update icon tooltip
            self.tray_icon.setToolTip("Thai ID Card Reader\nServer stopped")

    def open_web_interface(self):
        """Open web interface in browser."""
        if not self.server_manager.is_running():
            self.show_notification(
                "Server Not Running",
                "Please start the server first",
                QSystemTrayIcon.MessageIcon.Warning,
            )
            return

        url = self.settings.server_url
        logger.info(f"Opening web interface: {url}")
        webbrowser.open(url)

    def open_api_docs(self):
        """Open API documentation in browser."""
        if not self.server_manager.is_running():
            self.show_notification(
                "Server Not Running",
                "Please start the server first",
                QSystemTrayIcon.MessageIcon.Warning,
            )
            return

        url = f"{self.settings.server_url}/docs"
        logger.info(f"Opening API docs: {url}")
        webbrowser.open(url)

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            None,
            "About Thai ID Card Reader",
            "<h3>Thai ID Card Reader</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for reading Thai National ID cards "
            "with real-time streaming to web applications and Chrome extensions.</p>"
            "<p><b>Technology Stack:</b></p>"
            "<ul>"
            "<li>FastAPI for REST API and WebSocket server</li>"
            "<li>PySide6 for desktop GUI</li>"
            "<li>pythaiidcard library for card reading</li>"
            "</ul>"
            "<p>Visit the <a href='https://github.com/ninyawee/pythaiidcard'>GitHub repository</a> for more information.</p>",
        )

    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
    ):
        """
        Show a system tray notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Notification icon type
        """
        if self.settings.notifications_enabled:
            self.tray_icon.showMessage(title, message, icon, 3000)

    def quit_application(self):
        """Quit the application."""
        # Stop server if running
        if self.server_manager.is_running():
            logger.info("Stopping server before quit...")
            self.server_manager.stop()

        # Quit application
        logger.info("Quitting application")
        self.tray_icon.hide()
        QApplication.quit()

    def run(self):
        """Run the application main loop."""
        logger.info("Starting application event loop")
        sys.exit(self.app.exec())
