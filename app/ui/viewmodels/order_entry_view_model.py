"""Order entry view model."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.dto.order.order_entry_request import OrderEntryRequest, OrderSide, OrderType
from app.ui.viewmodels.base import ViewModelBase


class OrderEntryViewModel(ViewModelBase):
    """State for the embedded market order entry panel."""

    def __init__(self) -> None:
        super().__init__()
        self.symbol_code: str = ""
        self.side: OrderSide = "buy"
        self.order_type: OrderType = "limit"
        self.quantity: str = "1"
        self.price: str = ""
        self.trading_enabled: bool = False
        self.trading_status: str = ""
        self.error_message: str = ""
        self.result_message: str = ""
        self.last_success: bool = False

    def sync_symbol(self, symbol_code: str) -> None:
        """Update the symbol field from watchlist/chart selection."""
        normalized = symbol_code.strip()
        if not normalized or normalized == self.symbol_code:
            return
        self.symbol_code = normalized
        self.notify("symbol_code")

    def set_trading_status(self, *, enabled: bool, message: str) -> None:
        """Update trading availability for the panel."""
        self.trading_enabled = enabled
        self.trading_status = message
        self.notify("trading_status")

    def build_request(self) -> OrderEntryRequest:
        """Build an order entry request from the current form state."""
        price = "0" if self.order_type == "market" else self.price.strip()
        return OrderEntryRequest(
            symbol_code=self.symbol_code.strip(),
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity.strip(),
            price=price,
        )

    def estimated_amount(self) -> Decimal | None:
        """Return the estimated order amount for limit orders."""
        if self.order_type == "market":
            return None
        try:
            quantity = Decimal(self.quantity.strip())
            price = Decimal(self.price.strip())
        except (InvalidOperation, ValueError):
            return None
        if quantity <= 0 or price <= 0:
            return None
        return quantity * price

    def set_side(self, side: OrderSide) -> None:
        self.side = side
        self.notify("side")

    def set_order_type(self, order_type: OrderType) -> None:
        self.order_type = order_type
        if order_type == "market":
            self.price = "0"
        self.notify("order_type")

    def set_quantity(self, quantity: str) -> None:
        self.quantity = quantity
        self.notify("quantity")

    def set_price(self, price: str) -> None:
        self.price = price
        self.notify("price")

    def set_error_message(self, message: str) -> None:
        self.error_message = message
        self.notify("error_message")

    def clear_error_message(self) -> None:
        if not self.error_message:
            return
        self.error_message = ""
        self.notify("error_message")

    def set_result(self, *, success: bool, message: str) -> None:
        self.last_success = success
        self.result_message = message
        self.notify("result")

    def reset_form(self) -> None:
        """Reset mutable order fields while keeping the active symbol."""
        self.side = "buy"
        self.order_type = "limit"
        self.quantity = "1"
        self.price = ""
        self.error_message = ""
        self.result_message = ""
        self.last_success = False
        self.notify("reset")
