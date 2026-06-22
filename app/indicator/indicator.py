"""Indicator protocol."""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.chart.candle import Candle


class Indicator(Protocol):
    """Contract for candle-driven technical indicators."""

    def update(self, candle: Candle) -> None:
        """Apply a finalized candle to the indicator state."""
        ...

    def value(self) -> Decimal | None:
        """Return the latest indicator value, if available."""
        ...
