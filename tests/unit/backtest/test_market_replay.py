"""Market replay tests."""

from __future__ import annotations

import pytest
from tests.fixtures.backtest_fixtures import build_sample_provider

from app.backtest.market_replay_engine import MarketReplayEngine
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.events.in_memory_event_bus import InMemoryEventBus

pytestmark = pytest.mark.unit


def test_market_replay_publishes_all_bars() -> None:
    provider = build_sample_provider()
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    received: list = []
    event_bus.subscribe(EventType.MARKET_DATA, lambda event: received.append(event))

    replay = MarketReplayEngine(provider=provider, event_bus=event_bus)
    count = replay.replay()

    assert count == 5
    assert len(received) == 5
    assert received[0].payload["symbol_code"] == "005930"
