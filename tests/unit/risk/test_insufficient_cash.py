"""Insufficient cash risk tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_portfolio_service,
    build_test_risk_policy,
)

from app.risk.risk_evaluator import RiskEvaluator
from app.risk.risk_manager import RiskManager

pytestmark = pytest.mark.unit


def test_insufficient_cash_blocks_buy() -> None:
    portfolio_service = build_test_portfolio_service()
    evaluator = RiskEvaluator()
    manager = RiskManager()
    policy = build_test_risk_policy(max_order_amount=Decimal("100000000"))

    signal = build_test_buy_signal(price=Decimal("900000"), quantity=Decimal("1"))
    result = evaluator.evaluate(
        signal,
        portfolio=portfolio_service.get_snapshot(),
        policy=policy,
        manager=manager,
    )

    assert result.approved is False
    assert any(item.rule_code == "insufficient_cash" for item in result.violations)
