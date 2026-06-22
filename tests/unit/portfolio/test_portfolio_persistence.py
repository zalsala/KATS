"""Portfolio persistence tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.portfolio_fixtures import sample_account_payload

from app.events.domain_events import AccountEvent
from app.service.portfolio.portfolio_service import PortfolioService, build_portfolio_service

pytestmark = pytest.mark.unit


def test_apply_account_persists_snapshot(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_portfolio_repository()
    service = build_portfolio_service(
        account_no="12345678",
        portfolio_repository=repository,
    )

    service.apply_account(sample_account_payload())

    latest = repository.get_latest_snapshot("12345678")
    assert latest is not None
    assert latest.total_asset == Decimal("1750000")
    assert len(repository.list_positions("12345678")) == 1


def test_start_restores_latest_snapshot(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_portfolio_repository()
    writer = build_portfolio_service(
        account_no="12345678",
        portfolio_repository=repository,
    )
    writer.apply_account(sample_account_payload())

    reader = build_portfolio_service(
        account_no="12345678",
        portfolio_repository=repository,
    )
    reader.start(build_test_event_bus_service())

    snapshot = reader.get_snapshot()
    assert snapshot.total_asset == Decimal("1750000")
    assert snapshot.positions[0].symbol_code == "005930"


def test_service_without_repository_keeps_in_memory_behavior() -> None:
    service = PortfolioService(account_no="12345678")
    service.apply_account(sample_account_payload())

    snapshot = service.get_snapshot()
    assert snapshot.total_asset == Decimal("1750000")
    assert service.portfolio_repository is None


def test_event_handler_path_persists_snapshot(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_portfolio_repository()
    event_bus = build_test_event_bus_service()
    service = build_portfolio_service(
        event_bus=event_bus,
        account_no="12345678",
        portfolio_repository=repository,
    )
    service.start(event_bus)

    event_bus.publish(
        AccountEvent(
            source="test",
            event_name="account.updated",
            payload=sample_account_payload(),
        )
    )

    latest = repository.get_latest_snapshot("12345678")
    assert latest is not None
    assert latest.cash.orderable_cash == Decimal("800000")
