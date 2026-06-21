"""Historical data provider."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.domain.backtest.historical_bar import HistoricalBar


class HistoricalDataProvider:
    """Provides ordered historical bars for replay."""

    def __init__(self, bars: list[HistoricalBar]) -> None:
        self._bars = sorted(bars, key=lambda bar: bar.timestamp)

    def list_bars(self) -> tuple[HistoricalBar, ...]:
        """Return all bars in chronological order."""
        return tuple(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    @classmethod
    def from_prices(
        cls,
        *,
        symbol_code: str,
        prices: list[tuple[datetime, Decimal]],
    ) -> HistoricalDataProvider:
        """Build provider from ``(timestamp, price)`` tuples."""
        bars = [
            HistoricalBar(
                symbol_code=symbol_code,
                timestamp=timestamp,
                price=price,
            )
            for timestamp, price in prices
        ]
        return cls(bars)
