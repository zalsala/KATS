"""EMA indicator tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.unit.indicator.conftest import make_candle

from app.indicator.ema_indicator import EmaIndicator

pytestmark = pytest.mark.unit


def test_ema_returns_none_until_period_filled() -> None:
    indicator = EmaIndicator(3)

    indicator.update(make_candle(close="10", minute=1))
    indicator.update(make_candle(close="20", minute=2))
    assert indicator.value() is None


def test_ema_calculation() -> None:
    indicator = EmaIndicator(3)
    for close in ["10", "20", "30"]:
        indicator.update(make_candle(close=close, minute=1))

    assert indicator.value() == Decimal("20")

    indicator.update(make_candle(close="40", minute=2))
    assert indicator.value() == Decimal("30")


def test_ema_rolling_updates() -> None:
    indicator = EmaIndicator(2)
    indicator.update(make_candle(close="100", minute=1))
    indicator.update(make_candle(close="200", minute=2))
    assert indicator.value() == Decimal("150")

    indicator.update(make_candle(close="300", minute=3))
    assert indicator.value() == Decimal("250")
