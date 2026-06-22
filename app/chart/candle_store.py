"""Candle persistence contract."""

from __future__ import annotations

from typing import Protocol

from app.chart.candle import Candle


class CandleStore(Protocol):
    """Persistence contract for finalized candles."""

    def save_candle(self, candle: Candle) -> None:
        """Persist a finalized candle."""

    def load_candles(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int | None = None,
    ) -> list[Candle]:
        """Return stored candles ordered by timestamp ascending."""
