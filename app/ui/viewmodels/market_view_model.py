"""Market view model."""

from __future__ import annotations

from decimal import Decimal

from app.ui.viewmodels.base import ViewModelBase


class MarketViewModel(ViewModelBase):
    """State for the market view."""

    def __init__(self) -> None:
        super().__init__()
        self.symbol_code: str = ""
        self.symbol_input: str = "005930"
        self.current_price: Decimal | None = None
        self.last_updated: str = ""
        self.websocket_connected: bool = False
        self.subscribed_symbols: set[str] = set()
        self.status_message: str = ""

    def update_price(self, *, symbol_code: str, price: Decimal, updated_at: str = "") -> None:
        self.symbol_code = symbol_code
        self.current_price = price
        self.last_updated = updated_at
        self.notify("price")

    def set_symbol_input(self, symbol_code: str) -> None:
        self.symbol_input = symbol_code
        self.notify("symbol_input")

    def set_websocket_connected(self, connected: bool) -> None:
        self.websocket_connected = connected
        self.notify("websocket_connected")

    def add_subscription(self, symbol_code: str) -> None:
        self.subscribed_symbols.add(symbol_code)
        self.notify("subscribed_symbols")

    def remove_subscription(self, symbol_code: str) -> None:
        self.subscribed_symbols.discard(symbol_code)
        self.notify("subscribed_symbols")

    def set_status_message(self, message: str) -> None:
        self.status_message = message
        self.notify("status_message")
