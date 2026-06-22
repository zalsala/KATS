"""Account formatting tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.ui.formatting.account_formatting import (
    format_currency,
    format_signed_currency,
    format_signed_percent,
)

pytestmark = pytest.mark.unit


def test_currency_formatting() -> None:
    assert format_currency(Decimal("1500000")) == "1,500,000"


def test_profit_loss_formatting_positive() -> None:
    assert format_signed_currency(Decimal("50000")) == "+50,000"
    assert format_signed_percent(Decimal("7.14")) == "+7.14%"


def test_profit_loss_formatting_negative() -> None:
    assert format_signed_currency(Decimal("-12000")) == "-12,000"
    assert format_signed_percent(Decimal("-3.5")) == "-3.50%"


def test_profit_loss_formatting_zero() -> None:
    assert format_signed_currency(Decimal("0")) == "0"
    assert format_signed_percent(Decimal("0")) == "0.00%"
