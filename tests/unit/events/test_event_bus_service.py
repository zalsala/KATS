"""EventBusService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service

from app.core.logging.correlation import get_correlation_id
from app.events.domain_events import (
    ExecutionEvent,
    MarketDataEvent,
    OrderEvent,
    PortfolioEvent,
    StrategyEvent,
)
from app.events.event_types import EventType

pytestmark = pytest.mark.unit


class TestEventBusService:
    """Service-level EventBus tests."""

    def test_publish_and_subscribe(self) -> None:
        service = build_test_event_bus_service()
        symbols: list[str] = []

        service.subscribe(
            EventType.MARKET_DATA,
            lambda event: symbols.append(str(event.payload.get("symbol", ""))),
        )
        service.publish(
            MarketDataEvent(source="websocket", payload={"symbol": "005930", "price": "70000"})
        )

        assert symbols == ["005930"]

    def test_unsubscribe_via_service(self) -> None:
        service = build_test_event_bus_service()
        count = {"value": 0}

        sub_id = service.subscribe(
            EventType.ORDER,
            lambda _event: count.__setitem__("value", count["value"] + 1),
        )
        service.publish(OrderEvent(source="order"))
        service.unsubscribe(sub_id)
        service.publish(OrderEvent(source="order"))

        assert count["value"] == 1

    def test_publish_binds_correlation_context(self) -> None:
        service = build_test_event_bus_service()
        captured: list[str | None] = []

        service.subscribe(
            EventType.EXECUTION,
            lambda event: captured.append(get_correlation_id()),
        )
        event = ExecutionEvent(source="websocket", correlation_id="kats-test-correlation")
        service.publish(event)

        assert captured == ["kats-test-correlation"]

    def test_decoupled_modules_do_not_call_each_other(self) -> None:
        """WebSocket publishes market data; strategy handler reacts without direct calls."""
        service = build_test_event_bus_service()
        strategy_signals: list[str] = []
        portfolio_updates: list[str] = []

        service.subscribe(
            EventType.MARKET_DATA,
            lambda event: strategy_signals.append(event.payload["symbol"]),
        )
        service.subscribe(
            EventType.STRATEGY,
            lambda event: portfolio_updates.append(event.payload["action"]),
        )

        service.publish(MarketDataEvent(source="websocket", payload={"symbol": "005930"}))
        service.publish(
            StrategyEvent(source="strategy", payload={"action": "hold", "symbol": "005930"})
        )
        service.publish(PortfolioEvent(source="portfolio", payload={"action": "snapshot"}))

        assert strategy_signals == ["005930"]
        assert portfolio_updates == ["hold"]
