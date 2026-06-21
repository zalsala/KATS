"""PortfolioEngine tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.portfolio_fixtures import sample_account_payload

from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.events.in_memory_event_bus import InMemoryEventBus
from app.portfolio.in_memory_portfolio_store import InMemoryPortfolioStore
from app.portfolio.portfolio_engine import PortfolioEngine

pytestmark = pytest.mark.unit


def test_apply_account_sets_cash_and_holdings() -> None:
    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"))
    snapshot = engine.apply_account(sample_account_payload())

    assert snapshot.account_no == "12345678"
    assert snapshot.cash.total_deposit == Decimal("1000000")
    assert snapshot.cash.orderable_cash == Decimal("800000")
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].symbol_code == "005930"
    assert snapshot.positions[0].quantity == Decimal("10")


def test_apply_execution_buy_updates_average_price() -> None:
    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"))
    engine.apply_account(sample_account_payload())

    snapshot = engine.apply_execution(
        {
            "symbol_code": "005930",
            "stock_name": "삼성전자",
            "side": "02",
            "executed_quantity": "5",
            "executed_price": "76000",
        }
    )

    position = snapshot.positions[0]
    assert position.quantity == Decimal("15")
    assert position.average_price == Decimal("72000")


def test_apply_execution_sell_reduces_quantity() -> None:
    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"))
    engine.apply_account(sample_account_payload())

    snapshot = engine.apply_execution(
        {
            "symbol_code": "005930",
            "side": "01",
            "executed_quantity": "4",
            "executed_price": "76000",
        }
    )

    position = snapshot.positions[0]
    assert position.quantity == Decimal("6")
    assert position.average_price == Decimal("70000")


def test_apply_market_data_updates_evaluation() -> None:
    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"))
    engine.apply_account(sample_account_payload())

    snapshot = engine.apply_market_data({"symbol_code": "005930", "price": "80000"})

    position = snapshot.positions[0]
    assert position.current_price == Decimal("80000")
    assert position.evaluation_amount == Decimal("800000")
    assert position.profit_loss_amount == Decimal("100000")


def test_portfolio_totals_after_market_data() -> None:
    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"))
    engine.apply_account(sample_account_payload())
    snapshot = engine.apply_market_data({"symbol": "005930", "price": "80000"})

    assert snapshot.total_evaluation == Decimal("800000")
    assert snapshot.total_purchase == Decimal("700000")
    assert snapshot.total_profit_loss == Decimal("100000")
    assert snapshot.total_asset == Decimal("1800000")
    expected_rate = (Decimal("100000") / Decimal("700000")) * Decimal("100")
    assert snapshot.profit_rate == expected_rate


def test_engine_publishes_portfolio_event() -> None:
    bus = EventBusService(event_bus=InMemoryEventBus())
    received: list = []

    bus.subscribe(EventType.PORTFOLIO, lambda event: received.append(event))

    engine = PortfolioEngine(store=InMemoryPortfolioStore(account_no="12345678"), event_bus=bus)
    engine.apply_account(sample_account_payload())

    assert len(received) == 1
    assert received[0].event_type == "portfolio"
    assert received[0].payload["reason"] == "account_sync"
    assert received[0].payload["total_asset"] == "1750000"
