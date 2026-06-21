"""Stock price domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.market.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class StockPrice:
    """Current stock price snapshot.

    Attributes:
        symbol: Stock symbol value object.
        stock_name: Human-readable stock name.
        current_price: Current price.
        change_amount: Change amount versus previous close.
        change_rate: Change rate versus previous close.
        queried_at: Query timestamp in UTC.
    """

    symbol: Symbol
    stock_name: str
    current_price: Decimal
    change_amount: Decimal
    change_rate: Decimal
    queried_at: datetime
