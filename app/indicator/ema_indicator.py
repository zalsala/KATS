"""Exponential moving average indicator."""

from __future__ import annotations

from decimal import Decimal

from app.chart.candle import Candle


class EmaIndicator:
    """Exponential moving average over candle close prices."""

    def __init__(self, period: int) -> None:
        if period < 1:
            msg = "EMA period must be at least 1"
            raise ValueError(msg)
        self._period = period
        self._multiplier = Decimal("2") / Decimal(period + 1)
        self._sample_count = 0
        self._seed_sum = Decimal("0")
        self._value: Decimal | None = None

    @property
    def period(self) -> int:
        return self._period

    def update(self, candle: Candle) -> None:
        close = candle.close
        if self._value is None:
            self._sample_count += 1
            self._seed_sum += close
            if self._sample_count < self._period:
                return
            self._value = self._seed_sum / Decimal(self._period)
            return

        self._value = (close - self._value) * self._multiplier + self._value

    def value(self) -> Decimal | None:
        return self._value
