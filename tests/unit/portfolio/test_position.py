"""Position calculation tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.portfolio_fixtures import build_test_position

pytestmark = pytest.mark.unit


def test_position_evaluation_amount() -> None:
    position = build_test_position(quantity=Decimal("10"), current_price=Decimal("75000"))
    assert position.evaluation_amount == Decimal("750000")


def test_position_purchase_amount() -> None:
    position = build_test_position(quantity=Decimal("10"), average_price=Decimal("70000"))
    assert position.purchase_amount == Decimal("700000")


def test_position_profit_loss_amount() -> None:
    position = build_test_position()
    assert position.profit_loss_amount == Decimal("50000")


def test_position_profit_loss_rate() -> None:
    position = build_test_position()
    # 50000 / 700000 * 100 ≈ 7.142857...
    expected = (Decimal("50000") / Decimal("700000")) * Decimal("100")
    assert position.profit_loss_rate == expected


def test_position_profit_loss_rate_zero_purchase() -> None:
    position = build_test_position(quantity=Decimal("0"), average_price=Decimal("0"))
    assert position.profit_loss_rate == Decimal("0")


def test_position_apply_buy_average_price() -> None:
    position = build_test_position(quantity=Decimal("10"), average_price=Decimal("70000"))
    updated = position.apply_buy(Decimal("5"), Decimal("76000"))
    # (10*70000 + 5*76000) / 15 = 72000
    assert updated.quantity == Decimal("15")
    assert updated.average_price == Decimal("72000")
    assert updated.current_price == Decimal("76000")


def test_position_apply_sell_reduces_quantity() -> None:
    position = build_test_position()
    updated = position.apply_sell(Decimal("3"))
    assert updated is not None
    assert updated.quantity == Decimal("7")
    assert updated.average_price == Decimal("70000")


def test_position_apply_sell_closes_position() -> None:
    position = build_test_position(quantity=Decimal("10"))
    updated = position.apply_sell(Decimal("10"))
    assert updated is None


def test_position_with_price() -> None:
    position = build_test_position(current_price=Decimal("70000"))
    updated = position.with_price(Decimal("80000"))
    assert updated.current_price == Decimal("80000")
    assert updated.evaluation_amount == Decimal("800000")
