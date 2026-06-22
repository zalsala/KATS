"""Simple moving average indicator."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from app.chart.candle import Candle


class SmaIndicator:
    """Rolling simple moving average over candle close prices."""

    def __init__(self, period: int) -> None:
        if period < 1:
            msg = "SMA period must be at least 1"
            raise ValueError(msg)
        self._period = period
        self._closes: deque[Decimal] = deque(maxlen=period)
        self._value: Decimal | None = None

    @property
    def period(self) -> int:
        return self._period

    def update(self, candle: Candle) -> None:
        self._closes.append(candle.close)
        if len(self._closes) < self._period:
            self._value = None
            return
        self._value = sum(self._closes, Decimal("0")) / Decimal(self._period)

    def value(self) -> Decimal | None:
        return self._value
