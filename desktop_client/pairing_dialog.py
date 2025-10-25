"""Pairing dialog for Chrome extension integration."""

import logging
import requests
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QGroupBox,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .settings import Settings

logger = logging.getLogger(__name__)


class PairingDialog(QDialog):
    """Dialog for managing Chrome extension pairing and network settings."""

    def __init__(self, settings: Settings, parent=None):
        """
        Initialize the pairing dialog.

        Args:
            settings: Application settings instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Extension Pairing & Network Settings")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()

        # Passcode section
        passcode_group = QGroupBox("Extension Passcode")
        passcode_layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Use this passcode in your Chrome extension to connect to the card reader server."
        )
        instructions.setWordWrap(True)
        passcode_layout.addWidget(instructions)

        # Current passcode display
        passcode_display_layout = QHBoxLayout()
        passcode_label = QLabel("Current Passcode:")
        passcode_display_layout.addWidget(passcode_label)

        self.passcode_field = QLineEdit()
        self.passcode_field.setReadOnly(True)
        self.passcode_field.setFont(QFont("Courier", 12))
        self.passcode_field.setMinimumHeight(32)
        passcode_display_layout.addWidget(self.passcode_field)

        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_passcode)
        passcode_display_layout.addWidget(self.copy_button)

        passcode_layout.addLayout(passcode_display_layout)

        # Generate button
        generate_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate New Passcode")
        self.generate_button.clicked.connect(self.generate_new_passcode)
        generate_layout.addWidget(self.generate_button)
        generate_layout.addStretch()
        passcode_layout.addLayout(generate_layout)

        # Passcode creation info
        self.passcode_info_label = QLabel("")
        self.passcode_info_label.setWordWrap(True)
        self.passcode_info_label.setStyleSheet("color: #666; font-size: 10px;")
        passcode_layout.addWidget(self.passcode_info_label)

        passcode_group.setLayout(passcode_layout)
        layout.addWidget(passcode_group)

        # Network interface section
        network_group = QGroupBox("Network Interface")
        network_layout = QVBoxLayout()

        network_info = QLabel(
            "Select which network interface the server should bind to.\n"
            "For security, localhost (127.0.0.1) is recommended."
        )
        network_info.setWordWrap(True)
        network_layout.addWidget(network_info)

        interface_layout = QHBoxLayout()
        interface_label = QLabel("Bind to:")
        interface_layout.addWidget(interface_label)

        self.interface_combo = QComboBox()
        self.populate_interfaces()
        interface_layout.addWidget(self.interface_combo)

        network_layout.addLayout(interface_layout)

        restart_note = QLabel(
            "Note: Changing the network interface requires a server restart to take effect."
        )
        restart_note.setWordWrap(True)
        restart_note.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        network_layout.addWidget(restart_note)

        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_interfaces(self):
        """Populate the network interface combo box."""
        self.interface_combo.clear()

        interfaces = self.settings.get_available_interfaces()
        for display_name, ip_address in interfaces:
            self.interface_combo.addItem(display_name, ip_address)

    def load_current_settings(self):
        """Load and display current settings."""
        # Load passcode
        self.settings.load_passcode()

        if self.settings.passcode:
            self.passcode_field.setText(self.settings.passcode)

            if self.settings.passcode_created_at:
                self.passcode_info_label.setText(
                    f"Created: {self.settings.passcode_created_at}"
                )
        else:
            self.passcode_field.setText("No passcode configured")
            self.passcode_info_label.setText(
                "Click 'Generate New Passcode' to create one for your extension."
            )

        # Select current bind interface
        current_interface = self.settings.bind_interface
        for i in range(self.interface_combo.count()):
            if self.interface_combo.itemData(i) == current_interface:
                self.interface_combo.setCurrentIndex(i)
                break

    def copy_passcode(self):
        """Copy passcode to clipboard."""
        if self.settings.passcode:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.settings.passcode)

            QMessageBox.information(
                self,
                "Passcode Copied",
                "Passcode copied to clipboard.\n\n"
                "Paste it into your Chrome extension configuration.",
            )
        else:
            QMessageBox.warning(
                self,
                "No Passcode",
                "No passcode to copy. Generate one first.",
            )

    def generate_new_passcode(self):
        """Generate a new passcode via the API."""
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Generate New Passcode",
            "Are you sure you want to generate a new passcode?\n\n"
            "This will invalidate the old passcode and any extensions using it "
            "will need to be reconfigured.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            # Call API to generate passcode
            response = requests.post(
                f"{self.settings.server_url}/api/passcode/generate",
                params={"length": 10},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                new_passcode = data.get("passcode")
                created_at = data.get("created_at")

                # Update settings
                self.settings.passcode = new_passcode
                self.settings.passcode_created_at = created_at

                # Update UI
                self.passcode_field.setText(new_passcode)
                self.passcode_info_label.setText(f"Created: {created_at}")

                QMessageBox.information(
                    self,
                    "Passcode Generated",
                    f"New passcode generated successfully!\n\n"
                    f"Passcode: {new_passcode}\n\n"
                    f"Configure this in your Chrome extension to enable access.",
                )

                logger.info("New passcode generated successfully")

            else:
                QMessageBox.critical(
                    self,
                    "Generation Failed",
                    f"Failed to generate passcode: {response.text}",
                )
                logger.error(f"Passcode generation failed: {response.text}")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Server Not Running",
                "Cannot generate passcode - server is not running.\n\n"
                "Please start the server first.",
            )
            logger.error("Cannot generate passcode - server not running")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generating passcode: {str(e)}",
            )
            logger.error(f"Error generating passcode: {e}")

    def save_settings(self):
        """Save network interface settings."""
        selected_interface = self.interface_combo.currentData()

        if selected_interface != self.settings.bind_interface:
            # Interface changed - save and notify
            self.settings.bind_interface = selected_interface
            self.settings.save()

            QMessageBox.information(
                self,
                "Settings Saved",
                f"Network interface set to: {self.interface_combo.currentText()}\n\n"
                "Please restart the server for changes to take effect.",
            )

            logger.info(f"Network interface changed to: {selected_interface}")
        else:
            QMessageBox.information(
                self,
                "Settings Saved",
                "No changes to save.",
            )

    def closeEvent(self, event):
        """Handle dialog close event."""
        event.accept()
