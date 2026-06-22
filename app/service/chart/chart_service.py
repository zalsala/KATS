"""Chart data application service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.chart.candle import Candle
from app.chart.candle_builder import DEFAULT_INTERVAL, CandleBuilder
from app.chart.candle_store import CandleStore
from app.chart.in_memory_candle_store import InMemoryCandleStore


class ChartService:
    """Manage candle builders and persisted chart data per symbol."""

    def __init__(
        self,
        *,
        store: CandleStore | None = None,
        interval: str = DEFAULT_INTERVAL,
    ) -> None:
        self._store = store or InMemoryCandleStore()
        self._interval = interval
        self._builders: dict[str, CandleBuilder] = {}

    @property
    def store(self) -> CandleStore:
        return self._store

    def on_trade(
        self,
        symbol: str,
        price: Decimal | str | int | float,
        volume: int,
        *,
        timestamp: datetime,
    ) -> None:
        """Apply a trade tick and persist candles when a minute closes."""
        builder = self._builders.setdefault(
            symbol,
            CandleBuilder(symbol=symbol, interval=self._interval),
        )
        finalized = builder.update_trade(price, volume, timestamp=timestamp)
        if finalized is not None:
            self._store.save_candle(finalized)

    def get_candles(
        self,
        symbol: str,
        interval: str | None = None,
        *,
        limit: int | None = None,
        include_current: bool = True,
    ) -> list[Candle]:
        """Return stored candles, optionally including the in-progress candle."""
        resolved_interval = interval or self._interval
        candles = self._store.load_candles(symbol, resolved_interval)

        if include_current:
            builder = self._builders.get(symbol)
            current = builder.get_current_candle() if builder is not None else None
            if current is not None and current.interval == resolved_interval:
                candles = [*candles, current]

        if limit is not None:
            return candles[-limit:]
        return candles

    def finalize_symbol(self, symbol: str) -> Candle | None:
        """Finalize and persist the in-progress candle for a symbol."""
        builder = self._builders.get(symbol)
        if builder is None:
            return None
        finalized = builder.finalize()
        if finalized is not None:
            self._store.save_candle(finalized)
        return finalized


def build_chart_service(
    *,
    store: CandleStore | None = None,
    interval: str = DEFAULT_INTERVAL,
) -> ChartService:
    """Create a ChartService with default in-memory storage."""
    return ChartService(store=store, interval=interval)
