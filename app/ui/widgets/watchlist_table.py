"""Watchlist table widget."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from app.ui.models.watchlist_item import WatchlistItem

COLUMNS = ("Symbol", "Name", "Last Price", "Change %", "Status")
LIVE_COLOR = QColor("#66bb6a")
IDLE_COLOR = QColor("#9e9e9e")


class WatchlistTable(QTableWidget):
    """Scrollable single-selection watchlist table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self._row_by_symbol: dict[str, int] = {}

    def rebuild(self, items: list[WatchlistItem], *, selected_symbol: str | None) -> None:
        """Rebuild the table for a full watchlist update."""
        self.setRowCount(0)
        self._row_by_symbol.clear()
        for item in items:
            self._append_row(item)
        self._apply_selection(selected_symbol)

    def update_row(self, item: WatchlistItem) -> None:
        """Update a single row without rebuilding the full table."""
        row = self._row_by_symbol.get(item.symbol_code)
        if row is None:
            return
        self._set_row_values(row, item)

    def selected_symbol(self) -> str | None:
        """Return the currently selected symbol code."""
        rows = self.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.item(rows[0].row(), 0)
        return None if item is None else item.text()

    def select_symbol(self, symbol_code: str | None) -> None:
        """Highlight a row by symbol code."""
        self._apply_selection(symbol_code)

    def _append_row(self, item: WatchlistItem) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self._row_by_symbol[item.symbol_code] = row
        self._set_row_values(row, item)

    def _set_row_values(self, row: int, item: WatchlistItem) -> None:
        values = [
            item.symbol_code,
            item.name,
            _format_price(item.last_price),
            _format_change_percent(item.change_percent),
            "Live" if item.is_live else "-",
        ]
        for column, value in enumerate(values):
            cell = QTableWidgetItem(value)
            cell.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            if column in {2, 3}:
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
            if column == 4:
                cell.setForeground(LIVE_COLOR if item.is_live else IDLE_COLOR)
            self.setItem(row, column, cell)

    def _apply_selection(self, symbol_code: str | None) -> None:
        if symbol_code is None:
            self.clearSelection()
            return
        row = self._row_by_symbol.get(symbol_code)
        if row is None:
            return
        self.selectRow(row)


def _format_price(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}"


def _format_change_percent(value: Decimal | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"
