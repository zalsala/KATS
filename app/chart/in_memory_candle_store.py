"""In-memory candle store for tests and development."""

from __future__ import annotations

from copy import deepcopy

from app.chart.candle import Candle


class InMemoryCandleStore:
    """Thread-unsafe in-memory candle storage."""

    def __init__(self) -> None:
        self._candles: dict[tuple[str, str], list[Candle]] = {}

    def save_candle(self, candle: Candle) -> None:
        """Append a finalized candle for the symbol and interval."""
        key = (candle.symbol, candle.interval)
        rows = self._candles.setdefault(key, [])
        rows.append(deepcopy(candle))

    def load_candles(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int | None = None,
    ) -> list[Candle]:
        """Return stored candles ordered by timestamp ascending."""
        rows = list(self._candles.get((symbol, interval), []))
        rows.sort(key=lambda candle: candle.timestamp)
        if limit is None:
            return [deepcopy(candle) for candle in rows]
        return [deepcopy(candle) for candle in rows[-limit:]]
