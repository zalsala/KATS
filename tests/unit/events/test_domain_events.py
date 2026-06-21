"""BaseEvent and domain event tests."""

from __future__ import annotations

import pytest

from app.events.domain_events import (
    AccountEvent,
    ErrorEvent,
    ExecutionEvent,
    MarketDataEvent,
    OrderEvent,
    PortfolioEvent,
    RiskEvent,
    StrategyEvent,
    SystemEvent,
)
from app.events.event_types import EventType

pytestmark = pytest.mark.unit


class TestDomainEvents:
    """Tests for concrete domain events."""

    @pytest.mark.parametrize(
        ("event_cls", "event_type"),
        [
            (MarketDataEvent, EventType.MARKET_DATA),
            (OrderEvent, EventType.ORDER),
            (ExecutionEvent, EventType.EXECUTION),
            (AccountEvent, EventType.ACCOUNT),
            (PortfolioEvent, EventType.PORTFOLIO),
            (StrategyEvent, EventType.STRATEGY),
            (RiskEvent, EventType.RISK),
            (SystemEvent, EventType.SYSTEM),
            (ErrorEvent, EventType.ERROR),
        ],
    )
    def test_event_type_mapping(self, event_cls, event_type) -> None:
        event = event_cls(source="test", payload={"key": "value"})

        assert event.event_type == event_type
        assert event.source == "test"
        assert event.payload["key"] == "value"
        assert event.event_id
        assert event.correlation_id
