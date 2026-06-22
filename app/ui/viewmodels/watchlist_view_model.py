"""Watchlist view model."""

from __future__ import annotations

from decimal import Decimal

from app.ui.models.watchlist_item import WatchlistItem
from app.ui.viewmodels.base import ViewModelBase


class WatchlistViewModel(ViewModelBase):
    """State for the watchlist panel."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[WatchlistItem] = []
        self.selected_symbol: str | None = None
        self.error_message: str = ""

    def get_item(self, symbol_code: str) -> WatchlistItem | None:
        """Return a watchlist row by symbol code."""
        for item in self.items:
            if item.symbol_code == symbol_code:
                return item
        return None

    def set_items(self, items: list[WatchlistItem]) -> None:
        """Replace all watchlist rows."""
        self.items = list(items)
        self.notify("items")

    def set_selected_symbol(self, symbol_code: str | None) -> None:
        """Update the selected symbol and row highlight state."""
        self.selected_symbol = symbol_code
        for index, item in enumerate(self.items):
            live = item.symbol_code == symbol_code
            if item.is_live != live:
                self.items[index] = WatchlistItem(
                    symbol_code=item.symbol_code,
                    name=item.name,
                    last_price=item.last_price,
                    change_amount=item.change_amount,
                    change_percent=item.change_percent,
                    previous_close=item.previous_close,
                    is_live=live,
                )
                self.notify(f"row:{item.symbol_code}")
        self.notify("selected_symbol")

    def update_row_price(
        self,
        *,
        symbol_code: str,
        price: Decimal,
        change_amount: Decimal | None = None,
        change_percent: Decimal | None = None,
        is_live: bool = True,
    ) -> None:
        """Update quote fields for a single row."""
        for index, item in enumerate(self.items):
            if item.symbol_code != symbol_code:
                continue
            self.items[index] = WatchlistItem(
                symbol_code=item.symbol_code,
                name=item.name,
                last_price=price,
                change_amount=change_amount,
                change_percent=change_percent,
                previous_close=item.previous_close,
                is_live=is_live,
            )
            self.notify(f"row:{symbol_code}")
            return

    def set_error_message(self, message: str) -> None:
        """Set a user-facing validation or action error."""
        self.error_message = message
        self.notify("error_message")

    def clear_error_message(self) -> None:
        """Clear the current error message."""
        if not self.error_message:
            return
        self.error_message = ""
        self.notify("error_message")
