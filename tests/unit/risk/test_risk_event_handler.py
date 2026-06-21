"""RiskEngine EventBus integration tests."""

from __future__ import annotations

import pytest
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_risk_policy,
    build_test_risk_service,
    strategy_payload_from_signal,
)

from app.events.domain_events import RiskEvent, StrategyEvent
from app.events.event_types import EventType

pytestmark = pytest.mark.unit


def test_strategy_event_triggers_risk_validation() -> None:
    service, event_bus = build_test_risk_service(
        with_event_bus=True,
        policy=build_test_risk_policy(),
    )
    received: list = []
    event_bus.subscribe(EventType.RISK, lambda event: received.append(event))

    signal = build_test_buy_signal()
    event_bus.publish(
        StrategyEvent(
            source="strategy_engine",
            payload=strategy_payload_from_signal(signal),
        )
    )

    assert len(received) == 1
    assert isinstance(received[0], RiskEvent)
    assert received[0].payload["status"] == "APPROVED"


def test_rejected_signal_publishes_risk_event() -> None:
    service, event_bus = build_test_risk_service(with_event_bus=True)
    received: list = []
    event_bus.subscribe(EventType.RISK, lambda event: received.append(event))

    service.set_emergency_stop(True)
    signal = build_test_buy_signal()
    event_bus.publish(
        StrategyEvent(
            source="strategy_engine",
            payload=strategy_payload_from_signal(signal),
        )
    )

    assert received[0].payload["status"] == "REJECTED"
