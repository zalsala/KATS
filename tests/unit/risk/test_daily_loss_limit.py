"""Daily loss limit risk tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_portfolio_service,
    build_test_risk_policy,
)

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.risk.risk_evaluator import RiskEvaluator
from app.risk.risk_manager import RiskManager

pytestmark = pytest.mark.unit


def test_daily_loss_limit_blocks_orders() -> None:
    portfolio_service = build_test_portfolio_service()
    snapshot = portfolio_service.get_snapshot()
    manager = RiskManager()
    manager.ensure_daily_baseline(Decimal("2000000"))

    reduced = PortfolioSnapshot(
        account_no=snapshot.account_no,
        cash=snapshot.cash,
        positions=snapshot.positions,
        total_evaluation=Decimal("500000"),
        total_purchase=snapshot.total_purchase,
        total_profit_loss=Decimal("-500000"),
        total_asset=Decimal("1300000"),
        profit_rate=snapshot.profit_rate,
        updated_at=snapshot.updated_at,
    )

    evaluator = RiskEvaluator()
    policy = build_test_risk_policy(daily_loss_limit=Decimal("0.10"))
    result = evaluator.evaluate(
        build_test_buy_signal(price=Decimal("10000"), quantity=Decimal("1")),
        portfolio=reduced,
        policy=policy,
        manager=manager,
    )

    assert result.approved is False
    assert any(item.rule_code == "daily_loss_limit" for item in result.violations)
