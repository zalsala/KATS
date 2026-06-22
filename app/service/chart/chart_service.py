"""Chart data application service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.chart.candle import Candle
from app.chart.candle_builder import DEFAULT_INTERVAL, CandleBuilder
from app.chart.candle_store import CandleStore
from app.chart.chart_event_handler import ChartEventHandler
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.events.event_bus_service import EventBusService

logger = logging.getLogger(__name__)


class ChartService:
    """Manage candle builders and persisted chart data per symbol."""

    def __init__(
        self,
        *,
        store: CandleStore | None = None,
        interval: str = DEFAULT_INTERVAL,
        event_handler: ChartEventHandler | None = None,
        event_bus: EventBusService | None = None,
    ) -> None:
        self._store = store or InMemoryCandleStore()
        self._interval = interval
        self._builders: dict[str, CandleBuilder] = {}
        self._event_bus = event_bus
        self._handler = event_handler or ChartEventHandler(chart_service=self)
        self._started = False

    @property
    def store(self) -> CandleStore:
        return self._store

    @property
    def event_handler(self) -> ChartEventHandler:
        return self._handler

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Register chart handlers with EventBus."""
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start chart subscriptions"
            raise ValueError(msg)
        self._handler.register(bus)
        self._started = True
        logger.info("ChartService started with EventBus subscriptions")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unregister chart handlers from EventBus."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

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

    def on_market_tick(self, payload: dict[str, Any]) -> None:
        """Apply a MarketDataEvent payload as a realtime trade tick."""
        symbol = str(payload.get("symbol_code", payload.get("symbol", ""))).strip()
        if not symbol:
            return

        price_raw = payload.get("price", payload.get("current_price"))
        if price_raw is None:
            return

        volume = _extract_volume(payload)
        timestamp = _parse_market_timestamp(payload)
        self.on_trade(symbol, price_raw, volume, timestamp=timestamp)

    def on_realtime_trade(
        self,
        symbol: str,
        price: Decimal | str | int | float,
        volume: int,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Apply a realtime trade tick directly."""
        resolved_timestamp = timestamp or datetime.now(UTC)
        self.on_trade(symbol, price, volume, timestamp=resolved_timestamp)

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


def _extract_volume(payload: dict[str, Any]) -> int:
    raw = payload.get("volume", payload.get("executed_quantity", 1))
    if raw is None or raw == "":
        return 1
    return int(str(raw).replace(",", ""))


def _parse_market_timestamp(payload: dict[str, Any]) -> datetime:
    for key in ("timestamp", "received_at"):
        raw = payload.get(key)
        if raw is None:
            continue
        if isinstance(raw, datetime):
            return raw if raw.tzinfo is not None else raw.replace(tzinfo=UTC)
        if isinstance(raw, str) and raw:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    trade_time = payload.get("trade_time")
    if isinstance(trade_time, str) and len(trade_time) >= 6:
        now = datetime.now(UTC)
        return now.replace(
            hour=int(trade_time[0:2]),
            minute=int(trade_time[2:4]),
            second=int(trade_time[4:6]),
            microsecond=0,
        )

    return datetime.now(UTC)


def build_chart_service(
    *,
    store: CandleStore | None = None,
    interval: str = DEFAULT_INTERVAL,
    event_bus: EventBusService | None = None,
) -> ChartService:
    """Create a ChartService with default in-memory storage."""
    return ChartService(store=store, interval=interval, event_bus=event_bus)
