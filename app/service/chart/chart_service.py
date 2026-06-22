"""Chart data application service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.chart.candle import Candle
from app.chart.candle_builder import CandleBuilder
from app.chart.candle_store import CandleStore
from app.chart.chart_event_handler import ChartEventHandler
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.chart.timeframe import (
    DEFAULT_TIMEFRAME,
    SUPPORTED_TIMEFRAMES,
    Timeframe,
    resolve_timeframe,
)
from app.events.event_bus_service import EventBusService

logger = logging.getLogger(__name__)

BuilderKey = tuple[str, str]


class ChartService:
    """Manage candle builders and persisted chart data per symbol and timeframe."""

    def __init__(
        self,
        *,
        store: CandleStore | None = None,
        event_handler: ChartEventHandler | None = None,
        event_bus: EventBusService | None = None,
    ) -> None:
        self._store = store or InMemoryCandleStore()
        self._builders: dict[BuilderKey, CandleBuilder] = {}
        self._event_bus = event_bus
        self._handler = event_handler or ChartEventHandler(chart_service=self)
        self._started = False
        self._total_ticks = 0
        self._symbol_ticks: dict[str, int] = {}
        self._last_symbol = ""
        self._last_price = ""
        self._last_trade_time: datetime | None = None

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
        """Apply a trade tick to all supported timeframes for the symbol."""
        trade_price = Decimal(str(price).replace(",", ""))
        for timeframe in SUPPORTED_TIMEFRAMES:
            builder = self._get_builder(symbol, timeframe)
            finalized = builder.update_trade(price, volume, timestamp=timestamp)
            if finalized is not None:
                self._store.save_candle(finalized)
        self._record_trade(symbol, trade_price, timestamp)

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
        timeframe: str | Timeframe = DEFAULT_TIMEFRAME,
        *,
        limit: int | None = None,
        include_current: bool = True,
    ) -> list[Candle]:
        """Return stored candles for a symbol and timeframe."""
        resolved_timeframe = resolve_timeframe(timeframe).value
        candles = self._store.load_candles(symbol, resolved_timeframe)

        if include_current:
            builder = self._builders.get((symbol, resolved_timeframe))
            current = builder.get_current_candle() if builder is not None else None
            if current is not None and current.interval == resolved_timeframe:
                candles = [*candles, current]

        if limit is not None:
            return candles[-limit:]
        return candles

    def finalize_symbol(
        self,
        symbol: str,
        timeframe: str | Timeframe | None = None,
    ) -> Candle | None:
        """Finalize and persist in-progress candles for a symbol."""
        if timeframe is not None:
            return self._finalize_builder(symbol, resolve_timeframe(timeframe).value)

        last_finalized: Candle | None = None
        for supported in SUPPORTED_TIMEFRAMES:
            finalized = self._finalize_builder(symbol, supported.value)
            if finalized is not None:
                last_finalized = finalized
        return last_finalized

    def get_chart_stats(
        self,
        symbol: str | None = None,
        timeframe: str | Timeframe = DEFAULT_TIMEFRAME,
    ) -> dict[str, int | str]:
        """Return chart diagnostics for validation and UI observability."""
        resolved_timeframe = resolve_timeframe(timeframe).value
        if symbol is not None:
            ticks = self._symbol_ticks.get(symbol, 0)
            candles = len(self.get_candles(symbol, resolved_timeframe))
        else:
            ticks = self._total_ticks
            candles = sum(
                len(self.get_candles(sym, resolved_timeframe)) for sym in self._symbol_ticks
            )

        return {
            "ticks": ticks,
            "candles": candles,
            "symbols": len(self._symbol_ticks),
            "timeframe": resolved_timeframe,
            "last_symbol": self._last_symbol,
            "last_price": self._last_price,
            "last_trade_time": (
                self._last_trade_time.isoformat() if self._last_trade_time is not None else ""
            ),
        }

    def _get_builder(self, symbol: str, timeframe: Timeframe) -> CandleBuilder:
        key = (symbol, timeframe.value)
        return self._builders.setdefault(
            key,
            CandleBuilder(symbol=symbol, timeframe=timeframe),
        )

    def _finalize_builder(self, symbol: str, timeframe: str) -> Candle | None:
        builder = self._builders.get((symbol, timeframe))
        if builder is None:
            return None
        finalized = builder.finalize()
        if finalized is not None:
            self._store.save_candle(finalized)
        return finalized

    def _record_trade(self, symbol: str, price: Decimal, timestamp: datetime) -> None:
        self._total_ticks += 1
        self._symbol_ticks[symbol] = self._symbol_ticks.get(symbol, 0) + 1
        self._last_symbol = symbol
        self._last_price = str(price)
        self._last_trade_time = (
            timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=UTC)
        )


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
    event_bus: EventBusService | None = None,
) -> ChartService:
    """Create a ChartService with default in-memory storage."""
    return ChartService(store=store, event_bus=event_bus)
