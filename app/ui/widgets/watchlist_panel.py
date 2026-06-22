"""Watchlist panel widget."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.controllers.watchlist_controller import WatchlistController
from app.ui.viewmodels.watchlist_view_model import WatchlistViewModel
from app.ui.views.view_base import bind_view_model
from app.ui.widgets.watchlist_table import WatchlistTable


class WatchlistPanel(QWidget):
    """Watchlist management panel with live quote rows."""

    def __init__(
        self,
        *,
        view_model: WatchlistViewModel,
        controller: WatchlistController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller

        self._symbol_input = QLineEdit()
        self._symbol_input.setPlaceholderText("Add symbol (e.g. 005930)")
        self._add_button = QPushButton("Add")
        self._remove_button = QPushButton("Remove")
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef5350;")
        self._table = WatchlistTable()

        input_row = QHBoxLayout()
        input_row.addWidget(self._symbol_input, stretch=1)
        input_row.addWidget(self._add_button)
        input_row.addWidget(self._remove_button)

        layout = QVBoxLayout(self)
        layout.addLayout(input_row)
        layout.addWidget(self._error_label)
        layout.addWidget(self._table, stretch=1)

        self._add_button.clicked.connect(self._on_add_clicked)
        self._remove_button.clicked.connect(self._on_remove_clicked)
        self._symbol_input.returnPressed.connect(self._on_add_clicked)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        bind_view_model(self._vm, self._on_view_model_changed)
        self.refresh()

    def refresh(self) -> None:
        """Refresh the full watchlist table."""
        self._table.rebuild(self._vm.items, selected_symbol=self._vm.selected_symbol)
        self._error_label.setText(self._vm.error_message)

    def _on_view_model_changed(self, field: str) -> None:
        if field.startswith("row:"):
            symbol_code = field.removeprefix("row:")
            item = self._vm.get_item(symbol_code)
            if item is not None:
                self._table.update_row(item)
            return
        if field == "selected_symbol":
            self._table.select_symbol(self._vm.selected_symbol)
            return
        if field == "error_message":
            self._error_label.setText(self._vm.error_message)
            return
        if field == "items":
            self.refresh()

    def _on_add_clicked(self) -> None:
        self._controller.add_symbol(self._symbol_input.text())
        if not self._vm.error_message:
            self._symbol_input.clear()

    def _on_remove_clicked(self) -> None:
        self._controller.remove_selected()

    def _on_selection_changed(self) -> None:
        symbol_code = self._table.selected_symbol()
        if symbol_code is None or symbol_code == self._vm.selected_symbol:
            return
        self._controller.select_symbol(symbol_code)
