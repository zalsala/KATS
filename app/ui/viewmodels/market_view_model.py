"""Market view model."""

from __future__ import annotations

from decimal import Decimal

from app.ui.viewmodels.base import ViewModelBase


class MarketViewModel(ViewModelBase):
    """State for the market view."""

    def __init__(self) -> None:
        super().__init__()
        self.symbol_code: str = ""
        self.current_price: Decimal | None = None
        self.last_updated: str = ""

    def update_price(self, *, symbol_code: str, price: Decimal, updated_at: str = "") -> None:
        self.symbol_code = symbol_code
        self.current_price = price
        self.last_updated = updated_at
        self.notify("price")
