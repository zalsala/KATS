"""Application status bar widget."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStatusBar, QWidget


class KatsStatusBar(QStatusBar):
    """Status bar showing connection, emergency stop, and message."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._connection_label = QLabel("Disconnected")
        self._emergency_label = QLabel("Emergency: OFF")
        self._message_label = QLabel("Ready")
        self.addWidget(self._connection_label)
        self.addWidget(self._emergency_label)
        self.addPermanentWidget(self._message_label)

    def update_connection(self, status: str) -> None:
        self._connection_label.setText(f"Connection: {status}")

    def update_emergency_stop(self, active: bool) -> None:
        self._emergency_label.setText(f"Emergency: {'ON' if active else 'OFF'}")

    def update_message(self, message: str) -> None:
        self._message_label.setText(message)
