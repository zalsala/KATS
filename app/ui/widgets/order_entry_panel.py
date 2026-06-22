"""Embedded order entry panel for the market view."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.dto.order.order_entry_request import OrderSide, OrderType
from app.ui.controllers.order_entry_controller import OrderEntryController
from app.ui.viewmodels.order_entry_view_model import OrderEntryViewModel
from app.ui.views.view_base import bind_view_model


class OrderEntryPanel(QWidget):
    """Domestic stock cash order entry panel."""

    def __init__(
        self,
        *,
        view_model: OrderEntryViewModel,
        controller: OrderEntryController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller

        self._symbol = QLineEdit()
        self._side = QComboBox()
        self._side.addItems(["buy", "sell"])
        self._order_type = QComboBox()
        self._order_type.addItems(["limit", "market"])
        self._quantity = QLineEdit("1")
        self._price = QLineEdit()
        self._estimated_amount = QLabel("-")
        self._trading_status = QLabel("-")
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef5350;")
        self._result_label = QLabel("")
        self._submit_button = QPushButton("Submit Order")
        self._reset_button = QPushButton("Reset")

        self._symbol.textChanged.connect(self._on_symbol_changed)
        self._side.currentTextChanged.connect(self._on_side_changed)
        self._order_type.currentTextChanged.connect(self._on_order_type_changed)
        self._quantity.textChanged.connect(self._on_quantity_changed)
        self._price.textChanged.connect(self._on_price_changed)
        self._submit_button.clicked.connect(self._on_submit_clicked)
        self._reset_button.clicked.connect(self._on_reset_clicked)

        form = QFormLayout()
        form.addRow("Symbol", self._symbol)
        form.addRow("Side", self._side)
        form.addRow("Order Type", self._order_type)
        form.addRow("Quantity", self._quantity)
        form.addRow("Price", self._price)
        form.addRow("Estimated Amount", self._estimated_amount)
        form.addRow("Trading", self._trading_status)

        buttons = QHBoxLayout()
        buttons.addWidget(self._submit_button)
        buttons.addWidget(self._reset_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(self._result_label)
        layout.addLayout(buttons)

        bind_view_model(self._vm, self._on_view_model_changed)
        self.refresh()

    def refresh(self) -> None:
        """Refresh all panel fields from the view model."""
        self._symbol.setText(self._vm.symbol_code)
        self._side.setCurrentText(self._vm.side)
        self._order_type.setCurrentText(self._vm.order_type)
        self._quantity.setText(self._vm.quantity)
        self._price.setText(self._vm.price)
        self._price.setEnabled(self._vm.order_type == "limit")
        self._estimated_amount.setText(_format_amount(self._vm.estimated_amount()))
        self._trading_status.setText(self._vm.trading_status or "-")
        self._submit_button.setEnabled(self._vm.trading_enabled)
        self._error_label.setText(self._vm.error_message)
        self._result_label.setText(self._vm.result_message)

    def _on_view_model_changed(self, field: str) -> None:
        if field in {"symbol_code", "reset"}:
            self._symbol.setText(self._vm.symbol_code)
        if field in {"side", "reset"}:
            self._side.setCurrentText(self._vm.side)
        if field in {"order_type", "reset"}:
            self._order_type.setCurrentText(self._vm.order_type)
            self._price.setEnabled(self._vm.order_type == "limit")
            if self._vm.order_type == "market":
                self._price.setText("0")
        if field in {"quantity", "price", "order_type", "reset"}:
            self._quantity.setText(self._vm.quantity)
            self._price.setText(self._vm.price)
            self._estimated_amount.setText(_format_amount(self._vm.estimated_amount()))
        if field == "trading_status":
            self._trading_status.setText(self._vm.trading_status or "-")
            self._submit_button.setEnabled(self._vm.trading_enabled)
        if field == "error_message":
            self._error_label.setText(self._vm.error_message)
        if field == "result":
            self._result_label.setText(self._vm.result_message)

    def _on_symbol_changed(self, text: str) -> None:
        self._vm.symbol_code = text.strip()

    def _on_side_changed(self, text: str) -> None:
        if text in {"buy", "sell"}:
            self._vm.set_side(cast(OrderSide, text))

    def _on_order_type_changed(self, text: str) -> None:
        if text in {"limit", "market"}:
            self._vm.set_order_type(cast(OrderType, text))
            self._price.setEnabled(text == "limit")

    def _on_quantity_changed(self, text: str) -> None:
        self._vm.set_quantity(text)

    def _on_price_changed(self, text: str) -> None:
        self._vm.set_price(text)

    def _on_submit_clicked(self) -> None:
        self._controller.submit()

    def _on_reset_clicked(self) -> None:
        self._controller.reset()
        self.refresh()


def _format_amount(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}"
