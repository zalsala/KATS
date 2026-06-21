"""Dashboard view."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class DashboardView(QWidget):
    """Dashboard summary panel."""

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.dashboard
        self._connection = QLabel("-")
        self._emergency = QLabel("-")
        self._strategies = QLabel("-")
        self._total_asset = QLabel("-")
        self._profit = QLabel("-")
        self._cash = QLabel("-")

        form = QFormLayout()
        form.addRow("Connection", self._connection)
        form.addRow("Emergency Stop", self._emergency)
        form.addRow("Running Strategies", self._strategies)
        form.addRow("Total Asset", self._total_asset)
        form.addRow("Profit/Loss", self._profit)
        form.addRow("Cash", self._cash)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        self._connection.setText(self._vm.connection_status)
        self._emergency.setText("ON" if self._vm.emergency_stop else "OFF")
        self._strategies.setText(str(self._vm.running_strategy_count))
        if self._vm.summary is None:
            self._total_asset.setText("-")
            self._profit.setText("-")
            self._cash.setText("-")
            return
        summary = self._vm.summary
        self._total_asset.setText(str(summary.total_asset))
        self._profit.setText(f"{summary.total_profit_loss} ({summary.profit_rate}%)")
        self._cash.setText(str(summary.cash))
