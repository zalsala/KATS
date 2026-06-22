"""Embedded position panel for the market view."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.controllers.position_controller import PositionController
from app.ui.viewmodels.position_view_model import PositionViewModel
from app.ui.views.view_base import bind_view_model
from app.ui.widgets.position_table import PositionTable


class PositionPanel(QWidget):
    """Read-only domestic stock holdings panel."""

    def __init__(
        self,
        *,
        view_model: PositionViewModel,
        controller: PositionController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller

        self._status_label = QLabel("-")
        self._empty_label = QLabel("No holdings")
        self._empty_label.setStyleSheet("color: #9e9e9e;")
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef5350;")
        self._refresh_button = QPushButton("Refresh")
        self._table = PositionTable()

        header = QHBoxLayout()
        header.addWidget(QLabel("Positions"))
        header.addStretch(1)
        header.addWidget(self._refresh_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._status_label)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._error_label)
        layout.addWidget(self._table, stretch=1)

        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        bind_view_model(self._vm, self._on_view_model_changed)
        self.refresh()

    def refresh(self) -> None:
        """Refresh all panel fields from the view model."""
        self._status_label.setText(self._vm.lookup_status or "-")
        self._refresh_button.setEnabled(self._vm.lookup_enabled and not self._vm.loading)
        self._error_label.setText(self._vm.error_message)
        has_positions = bool(self._vm.positions)
        self._empty_label.setVisible(not has_positions and not self._vm.loading)
        self._table.setVisible(has_positions)
        if has_positions:
            self._table.rebuild(self._vm.positions, selected_symbol=self._vm.selected_symbol)

    def _on_view_model_changed(self, field: str) -> None:
        if field.startswith("row:"):
            symbol_code = field.removeprefix("row:")
            position = next(
                (item for item in self._vm.positions if item.symbol_code == symbol_code),
                None,
            )
            if position is not None:
                self._table.update_row(position, selected_symbol=self._vm.selected_symbol)
            return
        if field == "selected_symbol":
            self._table.highlight_symbol(self._vm.selected_symbol)
            return
        if field in {"positions", "loading", "lookup_status", "error_message"}:
            self.refresh()

    def _on_refresh_clicked(self) -> None:
        self._controller.refresh()
