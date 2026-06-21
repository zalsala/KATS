"""Historical market data bar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class HistoricalBar:
    """Single historical price point for replay."""

    symbol_code: str
    timestamp: datetime
    price: Decimal
    volume: Decimal = Decimal("0")
