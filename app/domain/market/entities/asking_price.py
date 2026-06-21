"""Asking price domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.market.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class PriceLevel:
    """Single bid or ask price level.

    Attributes:
        price: Price at the level.
        quantity: Quantity at the level.
        level: Level index starting at 1.
    """

    price: Decimal
    quantity: Decimal
    level: int


@dataclass(frozen=True, slots=True)
class AskingPrice:
    """Bid and ask price book snapshot.

    Attributes:
        symbol: Stock symbol value object.
        stock_name: Human-readable stock name.
        bid_levels: Bid price levels.
        ask_levels: Ask price levels.
        queried_at: Query timestamp in UTC.
    """

    symbol: Symbol
    stock_name: str
    bid_levels: tuple[PriceLevel, ...]
    ask_levels: tuple[PriceLevel, ...]
    queried_at: datetime
