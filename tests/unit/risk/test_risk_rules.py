"""Risk rule unit tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.portfolio_fixtures import sample_account_payload
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_portfolio_service,
    build_test_risk_policy,
)

from app.risk.risk_evaluator import RiskEvaluator
from app.risk.risk_manager import RiskManager

pytestmark = pytest.mark.unit


def test_max_order_amount_rule() -> None:
    portfolio_service = build_test_portfolio_service()
    evaluator = RiskEvaluator()
    manager = RiskManager()
    policy = build_test_risk_policy(max_order_amount=Decimal("50000"))

    signal = build_test_buy_signal(price=Decimal("70000"), quantity=Decimal("1"))
    result = evaluator.evaluate(
        signal,
        portfolio=portfolio_service.get_snapshot(),
        policy=policy,
        manager=manager,
    )

    assert result.approved is False
    assert any(item.rule_code == "max_order_amount" for item in result.violations)


def test_max_order_quantity_rule() -> None:
    portfolio_service = build_test_portfolio_service()
    evaluator = RiskEvaluator()
    manager = RiskManager()
    policy = build_test_risk_policy(max_order_quantity=Decimal("1"))

    signal = build_test_buy_signal(quantity=Decimal("5"))
    result = evaluator.evaluate(
        signal,
        portfolio=portfolio_service.get_snapshot(),
        policy=policy,
        manager=manager,
    )

    assert result.approved is False
    assert any(item.rule_code == "max_order_quantity" for item in result.violations)


def test_max_position_count_rule() -> None:
    portfolio_service = build_test_portfolio_service()
    portfolio_service.apply_account(
        {
            **sample_account_payload(),
            "holdings": [
                {
                    "symbol_code": "005930",
                    "quantity": "1",
                    "average_price": "100",
                    "current_price": "100",
                },
                {
                    "symbol_code": "000660",
                    "quantity": "1",
                    "average_price": "100",
                    "current_price": "100",
                },
                {
                    "symbol_code": "035420",
                    "quantity": "1",
                    "average_price": "100",
                    "current_price": "100",
                },
            ],
        }
    )
    evaluator = RiskEvaluator()
    manager = RiskManager()
    policy = build_test_risk_policy(max_position_count=3)

    signal = build_test_buy_signal(
        symbol_code="051910", price=Decimal("100"), quantity=Decimal("1")
    )
    result = evaluator.evaluate(
        signal,
        portfolio=portfolio_service.get_snapshot(),
        policy=policy,
        manager=manager,
    )

    assert result.approved is False
    assert any(item.rule_code == "max_position_count" for item in result.violations)
