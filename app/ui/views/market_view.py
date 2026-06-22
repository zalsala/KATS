"""Market view."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model
from app.ui.widgets.chart_widget import ChartWidget


class MarketView(QWidget):
    """Market data display panel."""

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.market
        self._chart_vm = view_model.chart
        self._symbol = QLabel("-")
        self._price = QLabel("-")
        self._updated = QLabel("-")
        self._chart_widget = ChartWidget()

        form = QFormLayout()
        form.addRow("Symbol", self._symbol)
        form.addRow("Price", self._price)
        form.addRow("Updated", self._updated)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._chart_widget, stretch=1)
        bind_view_model(self._vm, lambda _field: self.refresh())
        bind_view_model(self._chart_vm, lambda _field: self._update_chart_widget())
        self.refresh()
        self._load_chart()

    @property
    def chart_widget(self) -> ChartWidget:
        """Return the embedded chart widget."""
        return self._chart_widget

    def _update_chart_widget(self) -> None:
        self._chart_widget.set_candles(self._chart_vm.candles, symbol=self._chart_vm.symbol_code)

    def refresh(self) -> None:
        """Refresh quote labels."""
        self._symbol.setText(self._vm.symbol_code or self._chart_vm.symbol_code or "-")
        self._price.setText(str(self._vm.current_price) if self._vm.current_price else "-")
        self._updated.setText(self._vm.last_updated or "-")

    def _load_chart(self) -> None:
        """Load chart candles from ChartService via ChartViewModel."""
        self._chart_vm.refresh()
