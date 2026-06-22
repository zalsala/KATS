"""Position item calculation tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.position.position_item import PositionItem

pytestmark = pytest.mark.unit


def _sample_position() -> PositionItem:
    return PositionItem(
        symbol_code="005930",
        stock_name="삼성전자",
        quantity=Decimal("10"),
        average_price=Decimal("70000"),
        current_price=Decimal("75000"),
        evaluation_amount=Decimal("750000"),
        profit_loss_amount=Decimal("50000"),
        profit_loss_rate=Decimal("7.14"),
    )


def test_valuation_calculation() -> None:
    position = _sample_position().with_current_price(Decimal("80000"))

    assert position.evaluation_amount == Decimal("800000")


def test_unrealized_profit_loss_calculation() -> None:
    position = _sample_position().with_current_price(Decimal("80000"))

    assert position.profit_loss_amount == Decimal("100000")
    assert position.profit_loss_rate == Decimal("100000") / Decimal("700000") * Decimal("100")
