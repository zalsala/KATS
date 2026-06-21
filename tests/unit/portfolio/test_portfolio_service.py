"""PortfolioService tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.portfolio_fixtures import sample_account_payload

from app.service.portfolio.portfolio_service import PortfolioService, build_portfolio_service

pytestmark = pytest.mark.unit


def test_get_snapshot_returns_current_state() -> None:
    service = PortfolioService(account_no="12345678")
    service.apply_account(sample_account_payload())

    snapshot = service.get_snapshot()
    assert snapshot.account_no == "12345678"
    assert snapshot.total_asset == Decimal("1750000")


def test_start_registers_event_handlers() -> None:
    event_bus = build_test_event_bus_service()
    service = build_portfolio_service(event_bus=event_bus, account_no="12345678")
    service.start(event_bus)

    assert len(service.event_handler.subscription_ids) == 3


def test_apply_execution_via_service() -> None:
    service = PortfolioService(account_no="12345678")
    service.apply_account(sample_account_payload())
    service.apply_execution(
        {
            "symbol_code": "005930",
            "side": "01",
            "executed_quantity": "10",
            "executed_price": "75000",
        }
    )

    snapshot = service.get_snapshot()
    assert len(snapshot.positions) == 0


def test_apply_market_data_via_service() -> None:
    service = PortfolioService(account_no="12345678")
    service.apply_account(sample_account_payload())
    service.apply_market_data({"symbol_code": "005930", "price": "72000"})

    snapshot = service.get_snapshot()
    assert snapshot.positions[0].current_price == Decimal("72000")
