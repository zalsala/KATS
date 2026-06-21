"""Settings view."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class SettingsView(QWidget):
    """Settings display panel."""

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.settings
        self._environment = QLabel("-")
        self._account_type = QLabel("-")
        self._version = QLabel("-")

        form = QFormLayout()
        form.addRow("Environment", self._environment)
        form.addRow("Account Type", self._account_type)
        form.addRow("Version", self._version)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        self._environment.setText(self._vm.environment or "-")
        self._account_type.setText(self._vm.account_type or "-")
        self._version.setText(self._vm.application_version or "-")
