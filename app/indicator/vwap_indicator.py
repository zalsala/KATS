"""Volume-weighted average price indicator."""

from __future__ import annotations

from decimal import Decimal

from app.chart.candle import Candle


class VwapIndicator:
    """Intraday volume-weighted average price from finalized candles."""

    def __init__(self) -> None:
        self._session_date: str | None = None
        self._price_volume_sum = Decimal("0")
        self._volume_sum = 0
        self._value: Decimal | None = None

    def update(self, candle: Candle) -> None:
        session_date = candle.timestamp.date().isoformat()
        if self._session_date != session_date:
            self._session_date = session_date
            self._price_volume_sum = Decimal("0")
            self._volume_sum = 0
            self._value = None

        if candle.volume <= 0:
            return

        self._price_volume_sum += candle.close * Decimal(candle.volume)
        self._volume_sum += candle.volume
        self._value = self._price_volume_sum / Decimal(self._volume_sum)

    def value(self) -> Decimal | None:
        return self._value
