"""RealtimeMarketDataPublisher tests."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.domain.realtime.entities import RealtimeOrderbook, RealtimePrice
from app.events.domain_events import MarketDataEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.events.in_memory_event_bus import InMemoryEventBus
from app.realtime.realtime_market_data_publisher import (
    SOURCE,
    RealtimeMarketDataPublisher,
    build_realtime_market_data_publisher,
)

pytestmark = pytest.mark.unit

POLL_INTERVAL = 0.01
RECEIVE_TIMEOUT = 0.01


class FakeWebSocketService:
    """Minimal WebSocketService stand-in for publisher tests."""

    def __init__(self, *, connected: bool = True) -> None:
        self._connected = connected
        self._entities: list[RealtimePrice | RealtimeOrderbook | None] = []
        self.receive_error: Exception | None = None
        self.error_once = False
        self._error_raised = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def queue(self, entity: RealtimePrice | RealtimeOrderbook | None) -> None:
        self._entities.append(entity)

    def receive(self, timeout: float | None = None) -> RealtimePrice | RealtimeOrderbook | None:
        _ = timeout
        if self.error_once and not self._error_raised:
            self._error_raised = True
            if self.receive_error is not None:
                raise self.receive_error
            raise RuntimeError("receive failed")
        if self.receive_error is not None and not self.error_once:
            raise self.receive_error
        if not self._entities:
            return None
        return self._entities.pop(0)


def _price(symbol: str = "005930", price: str = "70000") -> RealtimePrice:
    return RealtimePrice(
        symbol_code=symbol,
        price=price,
        trade_time="120100",
        received_at=datetime(2024, 6, 20, 12, 1, tzinfo=UTC),
    )


def _orderbook(symbol: str = "005930") -> RealtimeOrderbook:
    return RealtimeOrderbook(
        symbol_code=symbol,
        ask_price="70100",
        ask_volume="10",
        bid_price="70000",
        bid_volume="20",
        received_at=datetime(2024, 6, 20, 12, 1, tzinfo=UTC),
    )


def _build_publisher(
    websocket: FakeWebSocketService,
) -> tuple[RealtimeMarketDataPublisher, EventBusService, list[MarketDataEvent]]:
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    received: list[MarketDataEvent] = []
    event_bus.subscribe(
        EventType.MARKET_DATA,
        lambda event: received.append(event),  # type: ignore[arg-type]
    )
    publisher = RealtimeMarketDataPublisher(
        websocket_service=websocket,  # type: ignore[arg-type]
        event_bus=event_bus,
        receive_timeout=RECEIVE_TIMEOUT,
        poll_interval_seconds=POLL_INTERVAL,
    )
    return publisher, event_bus, received


def _wait_until(predicate, *, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(POLL_INTERVAL)
    msg = "condition not met before timeout"
    raise AssertionError(msg)


def test_publisher_start_and_stop() -> None:
    websocket = FakeWebSocketService()
    publisher, _, _ = _build_publisher(websocket)

    publisher.start()
    assert publisher.is_running is True

    publisher.stop()
    assert publisher.is_running is False


def test_start_skipped_when_websocket_not_connected() -> None:
    websocket = FakeWebSocketService(connected=False)
    publisher, _, _ = _build_publisher(websocket)

    publisher.start()

    assert publisher.is_running is False


def test_receive_price_publishes_market_data_event() -> None:
    websocket = FakeWebSocketService()
    websocket.queue(_price(price="70300"))
    publisher, _, received = _build_publisher(websocket)

    publisher.start()
    _wait_until(lambda: len(received) == 1)
    publisher.stop()

    event = received[0]
    assert event.source == SOURCE
    assert event.event_name == "market_data.price.updated"
    assert event.payload["symbol_code"] == "005930"
    assert event.payload["price"] == "70300"


def test_receive_orderbook_publishes_market_data_event() -> None:
    websocket = FakeWebSocketService()
    websocket.queue(_orderbook())
    publisher, _, received = _build_publisher(websocket)

    publisher.start()
    _wait_until(lambda: len(received) == 1)
    publisher.stop()

    event = received[0]
    assert event.event_name == "market_data.orderbook.updated"
    assert event.payload["bid_price"] == "70000"
    assert event.payload["ask_price"] == "70100"


def test_receive_none_is_ignored() -> None:
    websocket = FakeWebSocketService()
    publisher, _, received = _build_publisher(websocket)

    publisher.start()
    time.sleep(RECEIVE_TIMEOUT + POLL_INTERVAL * 3)
    publisher.stop()

    assert received == []


def test_receive_exception_does_not_stop_publisher() -> None:
    websocket = FakeWebSocketService()
    websocket.error_once = True
    websocket.queue(_price(price="70400"))
    publisher, _, received = _build_publisher(websocket)

    publisher.start()
    _wait_until(lambda: len(received) == 1)
    assert publisher.is_running is True
    publisher.stop()


def test_stop_terminates_background_thread() -> None:
    websocket = FakeWebSocketService()
    publisher, _, _ = _build_publisher(websocket)

    publisher.start()
    thread = publisher._thread  # noqa: SLF001
    assert thread is not None
    publisher.stop()
    thread.join(timeout=1.0)

    assert not thread.is_alive()


def test_handles_100_messages() -> None:
    websocket = FakeWebSocketService()
    for index in range(100):
        websocket.queue(_price(price=str(70000 + index)))

    publisher, _, received = _build_publisher(websocket)
    publisher.start()
    _wait_until(lambda: len(received) >= 100, timeout=5.0)
    publisher.stop()

    assert len(received) == 100
    assert received[-1].payload["price"] == "70099"


def test_build_realtime_market_data_publisher() -> None:
    websocket = MagicMock()
    websocket.is_connected = True
    event_bus = EventBusService(event_bus=InMemoryEventBus())

    publisher = build_realtime_market_data_publisher(
        websocket_service=websocket,
        event_bus=event_bus,
    )

    assert isinstance(publisher, RealtimeMarketDataPublisher)
