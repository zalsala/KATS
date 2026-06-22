"""Watchlist domain model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class WatchlistItem:
    """Single watchlist row with quote and selection metadata."""

    symbol_code: str
    name: str
    last_price: Decimal | None = None
    change_amount: Decimal | None = None
    change_percent: Decimal | None = None
    previous_close: Decimal | None = None
    is_live: bool = False

    def copy(self) -> WatchlistItem:
        """Return a shallow copy of the row."""
        return WatchlistItem(
            symbol_code=self.symbol_code,
            name=self.name,
            last_price=self.last_price,
            change_amount=self.change_amount,
            change_percent=self.change_percent,
            previous_close=self.previous_close,
            is_live=self.is_live,
        )
