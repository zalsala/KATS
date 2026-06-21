"""Portfolio view."""

from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class PortfolioView(QWidget):
    """Portfolio holdings table."""

    _COLUMNS = (
        "Symbol",
        "Name",
        "Qty",
        "Avg",
        "Price",
        "Eval",
        "P/L",
        "P/L %",
    )

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.portfolio
        self._table = QTableWidget(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(list(self._COLUMNS))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        rows = self._vm.positions
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.symbol_code,
                row.stock_name,
                str(row.quantity),
                str(row.average_price),
                str(row.current_price),
                str(row.evaluation_amount),
                str(row.profit_loss_amount),
                str(row.profit_loss_rate),
            ]
            for col_index, value in enumerate(values):
                self._table.setItem(row_index, col_index, QTableWidgetItem(value))
