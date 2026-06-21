"""Market view."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class MarketView(QWidget):
    """Market data display panel."""

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.market
        self._symbol = QLabel("-")
        self._price = QLabel("-")
        self._updated = QLabel("-")

        form = QFormLayout()
        form.addRow("Symbol", self._symbol)
        form.addRow("Price", self._price)
        form.addRow("Updated", self._updated)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        self._symbol.setText(self._vm.symbol_code or "-")
        self._price.setText(str(self._vm.current_price) if self._vm.current_price else "-")
        self._updated.setText(self._vm.last_updated or "-")
