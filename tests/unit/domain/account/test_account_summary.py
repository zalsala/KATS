"""Account summary calculation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.account.account_summary import AccountSummary
from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.value_objects.account_context import AccountContext
from app.domain.position.position_item import PositionItem

pytestmark = pytest.mark.unit


def _sample_summary() -> AccountSummary:
    account = AccountContext(account_no="12345678", account_product="01")
    queried_at = datetime(2026, 6, 20, 9, 30, tzinfo=UTC)
    deposit = Deposit(
        account=account,
        total_deposit_amount=Decimal("2000000"),
        orderable_cash_amount=Decimal("1500000"),
        next_day_withdrawable_amount=Decimal("1800000"),
        queried_at=queried_at,
    )
    balance = AccountBalance(
        account=account,
        total_evaluation_amount=Decimal("10000000"),
        total_purchase_amount=Decimal("9000000"),
        total_profit_loss_amount=Decimal("1000000"),
        total_profit_loss_rate=Decimal("11.11"),
        queried_at=queried_at,
    )
    return AccountSummary.from_balance_and_deposit(balance=balance, deposit=deposit)


def test_with_positions_recalculates_totals() -> None:
    summary = _sample_summary()
    positions = [
        PositionItem(
            symbol_code="005930",
            stock_name="삼성전자",
            quantity=Decimal("10"),
            average_price=Decimal("70000"),
            current_price=Decimal("80000"),
            evaluation_amount=Decimal("800000"),
            profit_loss_amount=Decimal("100000"),
            profit_loss_rate=Decimal("14.29"),
        )
    ]

    updated = summary.with_positions(positions)

    assert updated.total_evaluation_amount == Decimal("2800000")
    assert updated.total_profit_loss_amount == Decimal("-8200000")
    assert updated.cash_balance == Decimal("2000000")
