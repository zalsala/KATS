"""PortfolioEventHandler EventBus integration tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.portfolio_fixtures import (
    build_test_portfolio_service_with_bus,
    sample_account_payload,
)

from app.events.domain_events import AccountEvent, ExecutionEvent, MarketDataEvent, PortfolioEvent
from app.events.event_types import EventType
from app.service.portfolio.portfolio_service import PortfolioService

pytestmark = pytest.mark.unit


def test_account_event_updates_portfolio() -> None:
    service, event_bus = build_test_portfolio_service_with_bus()
    event_bus.publish(AccountEvent(source="account_service", payload=sample_account_payload()))

    snapshot = service.get_snapshot()
    assert snapshot.cash.total_deposit == Decimal("1000000")
    assert len(snapshot.positions) == 1


def test_execution_event_applies_fill() -> None:
    service, event_bus = build_test_portfolio_service_with_bus()
    event_bus.publish(AccountEvent(source="account_service", payload=sample_account_payload()))
    event_bus.publish(
        ExecutionEvent(
            source="websocket_service",
            payload={
                "symbol_code": "005930",
                "side": "02",
                "executed_quantity": "2",
                "executed_price": "71000",
            },
        )
    )

    snapshot = service.get_snapshot()
    position = snapshot.positions[0]
    assert position.quantity == Decimal("12")
    expected_avg = (Decimal("10") * Decimal("70000") + Decimal("2") * Decimal("71000")) / Decimal(
        "12"
    )
    assert position.average_price == expected_avg


def test_market_data_event_updates_price() -> None:
    service, event_bus = build_test_portfolio_service_with_bus()
    event_bus.publish(AccountEvent(source="account_service", payload=sample_account_payload()))
    event_bus.publish(
        MarketDataEvent(
            source="websocket_service",
            payload={"symbol_code": "005930", "price": "78000"},
        )
    )

    snapshot = service.get_snapshot()
    assert snapshot.positions[0].current_price == Decimal("78000")
    assert snapshot.total_evaluation == Decimal("780000")


def test_portfolio_event_published_on_change() -> None:
    event_bus = build_test_event_bus_service()
    received: list = []

    event_bus.subscribe(EventType.PORTFOLIO, lambda event: received.append(event))

    service = PortfolioService(event_bus=event_bus, account_no="12345678")
    service.start(event_bus)
    service.apply_account(sample_account_payload())

    assert len(received) == 1
    assert isinstance(received[0], PortfolioEvent)
    assert received[0].payload["reason"] == "account_sync"
