"""Chart realtime integration tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.events.domain_events import MarketDataEvent
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.service.chart.chart_service import ChartService

pytestmark = pytest.mark.unit

SYMBOL = "005930"


def _ts(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 6, 20, 12, minute, second, tzinfo=UTC)


def _build_started_service(
    *,
    store: InMemoryCandleStore | None = None,
) -> tuple[ChartService, EventBusService]:
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    service = ChartService(store=store or InMemoryCandleStore(), event_bus=event_bus)
    service.start(event_bus)
    return service, event_bus


def _publish_tick(
    event_bus: EventBusService,
    *,
    price: str,
    volume: str,
    timestamp: datetime,
) -> None:
    event_bus.publish(
        MarketDataEvent(
            source="websocket",
            payload={
                "symbol_code": SYMBOL,
                "price": price,
                "volume": volume,
                "timestamp": timestamp.isoformat(),
            },
        )
    )


def test_market_data_event_updates_chart_service() -> None:
    service, event_bus = _build_started_service()

    _publish_tick(event_bus, price="70000", volume="10", timestamp=_ts(1, 3))

    candles = service.get_candles(SYMBOL)
    assert len(candles) == 1
    assert candles[0].close == Decimal("70000")
    assert candles[0].volume == 10


def test_same_minute_updates_existing_candle() -> None:
    service, event_bus = _build_started_service()

    _publish_tick(event_bus, price="70000", volume="10", timestamp=_ts(1, 3))
    _publish_tick(event_bus, price="70500", volume="5", timestamp=_ts(1, 40))

    candle = service.get_candles(SYMBOL)[0]
    assert candle.volume == 15
    assert candle.close == Decimal("70500")


def test_next_minute_creates_new_candle() -> None:
    store = InMemoryCandleStore()
    service, event_bus = _build_started_service(store=store)

    _publish_tick(event_bus, price="70000", volume="10", timestamp=_ts(1, 50))
    _publish_tick(event_bus, price="71000", volume="3", timestamp=_ts(2, 0))

    stored = store.load_candles(SYMBOL, "1m")
    current = service.get_candles(SYMBOL, include_current=True)[-1]

    assert len(stored) == 1
    assert stored[0].timestamp == _ts(1)
    assert current.timestamp == _ts(2)
    assert current.volume == 3


def test_on_market_tick_skips_invalid_payload() -> None:
    service = ChartService(store=InMemoryCandleStore())

    service.on_market_tick({})
    service.on_market_tick({"symbol_code": "005930"})
    service.on_market_tick({"price": "70000"})

    assert service.get_candles(SYMBOL) == []


def test_on_realtime_trade_delegates_to_on_trade() -> None:
    service = ChartService(store=InMemoryCandleStore())

    service.on_realtime_trade(SYMBOL, "70100", 4, timestamp=_ts(1, 10))

    candle = service.get_candles(SYMBOL)[0]
    assert candle.close == Decimal("70100")
    assert candle.volume == 4


def test_handles_100_realtime_events() -> None:
    service, event_bus = _build_started_service()

    for index in range(100):
        second = index % 60
        minute = 1 + index // 60
        _publish_tick(
            event_bus,
            price=str(70000 + index),
            volume="1",
            timestamp=datetime(2024, 6, 20, 12, minute, second, tzinfo=UTC),
        )

    candles = service.get_candles(SYMBOL)
    assert len(candles) >= 2
    assert candles[-1].close == Decimal("70099")
    assert sum(candle.volume for candle in candles) == 100
