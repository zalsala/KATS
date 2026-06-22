"""SMA indicator tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.unit.indicator.conftest import make_candle

from app.indicator.sma_indicator import SmaIndicator

pytestmark = pytest.mark.unit


def test_sma_returns_none_until_period_filled() -> None:
    indicator = SmaIndicator(3)

    indicator.update(make_candle(close="10", minute=1))
    assert indicator.value() is None

    indicator.update(make_candle(close="20", minute=2))
    assert indicator.value() is None


def test_sma_calculation() -> None:
    indicator = SmaIndicator(5)
    closes = ["10", "20", "30", "40", "50"]

    for index, close in enumerate(closes, start=1):
        indicator.update(make_candle(close=close, minute=index))

    assert indicator.value() == Decimal("30")


def test_sma_rolling_window() -> None:
    indicator = SmaIndicator(3)
    for close in ["10", "20", "30"]:
        indicator.update(make_candle(close=close, minute=1))
    assert indicator.value() == Decimal("20")

    indicator.update(make_candle(close="40", minute=2))
    assert indicator.value() == Decimal("30")
