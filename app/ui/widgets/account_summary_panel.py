"""Embedded account summary panel for the market view."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.controllers.account_summary_controller import AccountSummaryController
from app.ui.formatting.account_formatting import (
    format_currency,
    format_signed_currency,
    format_signed_percent,
)
from app.ui.viewmodels.account_summary_view_model import AccountSummaryViewModel
from app.ui.views.view_base import bind_view_model


class AccountSummaryPanel(QWidget):
    """Read-only domestic stock account summary panel."""

    def __init__(
        self,
        *,
        view_model: AccountSummaryViewModel,
        controller: AccountSummaryController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller

        self._status_label = QLabel("-")
        self._loading_label = QLabel("")
        self._empty_label = QLabel("Account summary is not configured")
        self._empty_label.setStyleSheet("color: #9e9e9e;")
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef5350;")
        self._refresh_button = QPushButton("Refresh")

        self._cash_balance = QLabel("-")
        self._buying_power = QLabel("-")
        self._total_evaluation = QLabel("-")
        self._total_purchase = QLabel("-")
        self._total_pl = QLabel("-")
        self._total_pl_rate = QLabel("-")
        self._last_refreshed = QLabel("-")

        header = QHBoxLayout()
        header.addWidget(QLabel("Account Summary"))
        header.addStretch(1)
        header.addWidget(self._refresh_button)

        form = QFormLayout()
        form.addRow("Cash Balance", self._cash_balance)
        form.addRow("Buying Power", self._buying_power)
        form.addRow("Total Evaluation", self._total_evaluation)
        form.addRow("Total Purchase", self._total_purchase)
        form.addRow("Total Unrealized P/L", self._total_pl)
        form.addRow("Total Unrealized P/L %", self._total_pl_rate)
        form.addRow("Last Refreshed", self._last_refreshed)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._status_label)
        layout.addWidget(self._loading_label)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._error_label)
        layout.addLayout(form)

        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        bind_view_model(self._vm, self._on_view_model_changed)
        self.refresh()

    def refresh(self) -> None:
        """Refresh all panel fields from the view model."""
        self._status_label.setText(self._vm.lookup_status or "-")
        self._refresh_button.setEnabled(self._vm.lookup_enabled and not self._vm.loading)
        self._loading_label.setText("Loading..." if self._vm.loading else "")
        self._error_label.setText(self._vm.error_message)

        summary = self._vm.summary
        has_summary = summary is not None
        self._empty_label.setVisible(
            not has_summary and not self._vm.loading and not self._vm.error_message
        )

        if not has_summary:
            self._set_values_empty()
            return

        assert summary is not None
        self._cash_balance.setText(format_currency(summary.cash_balance))
        self._buying_power.setText(format_currency(summary.available_buying_power))
        self._total_evaluation.setText(format_currency(summary.total_evaluation_amount))
        self._total_purchase.setText(format_currency(summary.total_purchase_amount))
        self._total_pl.setText(format_signed_currency(summary.total_profit_loss_amount))
        self._total_pl_rate.setText(format_signed_percent(summary.total_profit_loss_rate))
        self._last_refreshed.setText(summary.last_refreshed_at.isoformat())

    def _set_values_empty(self) -> None:
        self._cash_balance.setText("-")
        self._buying_power.setText("-")
        self._total_evaluation.setText("-")
        self._total_purchase.setText("-")
        self._total_pl.setText("-")
        self._total_pl_rate.setText("-")
        self._last_refreshed.setText("-")

    def _on_view_model_changed(self, field: str) -> None:
        if field in {"summary", "loading", "lookup_status", "error_message"}:
            self.refresh()

    def _on_refresh_clicked(self) -> None:
        self._controller.refresh()
