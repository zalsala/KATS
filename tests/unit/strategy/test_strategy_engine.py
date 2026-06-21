"""StrategyEngine execution tests."""

from __future__ import annotations

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.strategy_fixtures import (
    build_test_strategy_service,
    register_and_start_strategy,
    sample_market_data_payload,
)

from app.events.domain_events import MarketDataEvent, StrategyEvent
from app.events.event_types import EventType
from app.service.strategy.strategy_service import StrategyService

pytestmark = pytest.mark.unit


def test_strategy_engine_publishes_strategy_event() -> None:
    event_bus = build_test_event_bus_service()
    received: list = []
    event_bus.subscribe(EventType.STRATEGY, lambda event: received.append(event))

    service = StrategyService(event_bus=event_bus)
    register_and_start_strategy(service, strategy_type="buy_and_hold", name="bh")
    service.handle_market_data(sample_market_data_payload())

    assert len(received) == 1
    assert isinstance(received[0], StrategyEvent)
    assert received[0].payload["signal_type"] == "BUY"


def test_eventbus_integration_market_data_triggers_strategy() -> None:
    service, event_bus = build_test_strategy_service(with_event_bus=True)
    register_and_start_strategy(service, strategy_type="buy_and_hold", name="bh")

    event_bus.publish(
        MarketDataEvent(
            source="websocket_service",
            payload=sample_market_data_payload(price="70500"),
        )
    )

    managed = service.manager.list_managed()[0]
    stats = managed.entity.statistics
    assert stats is not None
    assert stats.market_data_count == 1
    assert stats.buy_signals == 1


def test_multiple_strategies_run_in_parallel() -> None:
    service = StrategyService()
    register_and_start_strategy(service, strategy_type="buy_and_hold", name="bh-1")
    register_and_start_strategy(
        service,
        strategy_type="moving_average_cross",
        name="ma-1",
        parameters={"short_period": 2, "long_period": 3},
    )

    results = service.handle_market_data(sample_market_data_payload(price="70000"))
    assert len(results) == 1

    for _ in range(5):
        service.handle_market_data(sample_market_data_payload(price="70100"))

    assert len(service.manager.list_managed()) == 2
