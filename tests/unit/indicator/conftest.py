"""Indicator test helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.chart.candle import Candle


def make_candle(
    *,
    symbol: str = "005930",
    interval: str = "1m",
    minute: int = 1,
    close: str | Decimal = "100",
    volume: int = 10,
    day: int = 20,
) -> Candle:
    """Build a test candle with a single close price."""
    price = Decimal(str(close))
    return Candle(
        symbol=symbol,
        interval=interval,
        timestamp=datetime(2024, 6, day, 12, minute, 0, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=volume,
    )
