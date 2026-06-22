"""Position holdings table widget."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from app.domain.position.position_item import PositionItem

COLUMNS = (
    "Symbol",
    "Name",
    "Qty",
    "Avg Price",
    "Current",
    "Eval Amt",
    "P/L",
    "P/L %",
)
HIGHLIGHT_COLOR = QColor("#1e3a5f")


class PositionTable(QTableWidget):
    """Read-only holdings table with selected-symbol highlighting."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self._row_by_symbol: dict[str, int] = {}

    def rebuild(self, positions: list[PositionItem], *, selected_symbol: str) -> None:
        """Rebuild the table for a full holdings update."""
        self.setRowCount(0)
        self._row_by_symbol.clear()
        for position in positions:
            self._append_row(position)
        self._apply_highlight(selected_symbol)

    def update_row(self, position: PositionItem, *, selected_symbol: str) -> None:
        """Update a single row without rebuilding the full table."""
        row = self._row_by_symbol.get(position.symbol_code)
        if row is None:
            return
        self._set_row_values(row, position)
        self._apply_highlight(selected_symbol)

    def highlight_symbol(self, symbol_code: str) -> None:
        """Highlight the row matching the active watchlist/chart symbol."""
        self._apply_highlight(symbol_code)

    def _append_row(self, position: PositionItem) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self._row_by_symbol[position.symbol_code] = row
        self._set_row_values(row, position)

    def _set_row_values(self, row: int, position: PositionItem) -> None:
        values = [
            position.symbol_code,
            position.stock_name,
            _format_decimal(position.quantity, 0),
            _format_decimal(position.average_price),
            _format_decimal(position.current_price),
            _format_decimal(position.evaluation_amount, 0),
            _format_signed_decimal(position.profit_loss_amount, 0),
            _format_signed_percent(position.profit_loss_rate),
        ]
        for column, value in enumerate(values):
            cell = QTableWidgetItem(value)
            cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if column >= 2:
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
            self.setItem(row, column, cell)

    def _apply_highlight(self, selected_symbol: str) -> None:
        normalized = selected_symbol.strip()
        for row in range(self.rowCount()):
            symbol_item = self.item(row, 0)
            symbol = "" if symbol_item is None else symbol_item.text()
            highlighted = bool(normalized) and symbol == normalized
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is None:
                    continue
                item.setBackground(HIGHLIGHT_COLOR if highlighted else QColor())


def _format_decimal(value: Decimal, places: int = 0) -> str:
    if places == 0:
        return f"{value:,.0f}"
    return f"{value:,.{places}f}"


def _format_signed_decimal(value: Decimal, places: int = 0) -> str:
    formatted = _format_decimal(value, places)
    if value > 0:
        return f"+{formatted}"
    return formatted


def _format_signed_percent(value: Decimal) -> str:
    formatted = f"{value:.2f}%"
    if value > 0:
        return f"+{formatted}"
    return formatted
