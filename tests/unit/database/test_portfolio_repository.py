"""Portfolio repository tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.domain.portfolio.cash_balance import CashBalance
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.portfolio.position import Position

pytestmark = pytest.mark.unit


def _build_snapshot() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account_no="1234567890",
        cash=CashBalance(total_deposit=Decimal("1000000"), orderable_cash=Decimal("900000")),
        positions=(
            Position(
                symbol_code="005930",
                stock_name="Samsung",
                quantity=Decimal("10"),
                average_price=Decimal("70000"),
                current_price=Decimal("71000"),
            ),
        ),
        total_evaluation=Decimal("710000"),
        total_purchase=Decimal("700000"),
        total_profit_loss=Decimal("10000"),
        total_asset=Decimal("1710000"),
        profit_rate=Decimal("0.014"),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def test_portfolio_repository_save_positions_and_snapshot(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_portfolio_repository()
    snapshot = _build_snapshot()
    repository.save_positions(snapshot.account_no, list(snapshot.positions))
    positions = repository.list_positions(snapshot.account_no)
    assert len(positions) == 1
    assert positions[0].symbol_code == "005930"
    snapshot_id = repository.save_snapshot(snapshot)
    assert snapshot_id > 0
    latest = repository.get_latest_snapshot(snapshot.account_no)
    assert latest is not None
    assert latest.total_asset == snapshot.total_asset
