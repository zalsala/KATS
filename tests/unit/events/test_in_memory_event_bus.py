"""InMemoryEventBus tests."""

from __future__ import annotations

import threading

import pytest

from app.events.dead_letter_queue import DeadLetterQueue
from app.events.domain_events import MarketDataEvent, OrderEvent
from app.events.event_types import EventType
from app.events.in_memory_event_bus import InMemoryEventBus

pytestmark = pytest.mark.unit


class TestInMemoryEventBusPublish:
    """Publish tests."""

    def test_publish_delivers_to_subscriber(self) -> None:
        bus = InMemoryEventBus()
        received: list[str] = []

        bus.subscribe(EventType.MARKET_DATA, lambda event: received.append(event.event_name))
        bus.publish(MarketDataEvent(source="websocket", payload={"symbol": "005930"}))

        assert received == ["market_data.updated"]

    def test_publish_with_no_subscribers_is_safe(self) -> None:
        bus = InMemoryEventBus()

        bus.publish(OrderEvent(source="order"))


class TestInMemoryEventBusSubscribe:
    """Subscribe and unsubscribe tests."""

    def test_unsubscribe_stops_delivery(self) -> None:
        bus = InMemoryEventBus()
        received: list[str] = []

        def handler(event) -> None:
            received.append(event.event_id)

        sub_id = bus.subscribe(EventType.ORDER, handler)
        event = OrderEvent(source="order")
        bus.publish(event)
        assert len(received) == 1

        assert bus.unsubscribe(sub_id) is True
        bus.publish(OrderEvent(source="order"))
        assert len(received) == 1

    def test_unsubscribe_unknown_returns_false(self) -> None:
        bus = InMemoryEventBus()

        assert bus.unsubscribe("missing-id") is False


class TestInMemoryEventBusMultipleHandlers:
    """Multiple handler tests."""

    def test_multiple_handlers_receive_same_event(self) -> None:
        bus = InMemoryEventBus()
        first: list[str] = []
        second: list[str] = []

        bus.subscribe(EventType.MARKET_DATA, lambda event: first.append("first"))
        bus.subscribe(EventType.MARKET_DATA, lambda event: second.append("second"))
        bus.publish(MarketDataEvent(source="market"))

        assert first == ["first"]
        assert second == ["second"]


class TestInMemoryEventBusErrorHandling:
    """Error handler and dead letter queue tests."""

    def test_failed_handler_goes_to_dead_letter_queue(self) -> None:
        dlq = DeadLetterQueue()
        bus = InMemoryEventBus(dead_letter_queue=dlq)
        received: list[str] = []

        def failing_handler(_event) -> None:
            msg = "handler failed"
            raise RuntimeError(msg)

        def ok_handler(_event) -> None:
            received.append("ok")

        bus.subscribe(EventType.ORDER, failing_handler)
        bus.subscribe(EventType.ORDER, ok_handler)
        bus.publish(OrderEvent(source="order"))

        assert received == ["ok"]
        assert dlq.size() == 1
        assert "handler failed" in dlq.all()[0].error


class TestInMemoryEventBusThreadSafety:
    """Thread safety tests."""

    def test_concurrent_publish_and_subscribe(self) -> None:
        bus = InMemoryEventBus()
        lock = threading.Lock()
        count = {"value": 0}

        def handler(_event) -> None:
            with lock:
                count["value"] += 1

        bus.subscribe(EventType.MARKET_DATA, handler)

        def publish_many() -> None:
            for _ in range(20):
                bus.publish(MarketDataEvent(source="ws"))

        threads = [threading.Thread(target=publish_many) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert count["value"] == 100
