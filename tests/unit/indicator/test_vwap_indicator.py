"""VWAP indicator tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.unit.indicator.conftest import make_candle

from app.indicator.vwap_indicator import VwapIndicator

pytestmark = pytest.mark.unit


def test_vwap_calculation() -> None:
    indicator = VwapIndicator()

    indicator.update(make_candle(close="100", volume=10, minute=1))
    assert indicator.value() == Decimal("100")

    indicator.update(make_candle(close="200", volume=20, minute=2))
    assert indicator.value() == Decimal("5000") / Decimal("30")


def test_vwap_resets_intraday() -> None:
    indicator = VwapIndicator()

    indicator.update(make_candle(close="100", volume=10, minute=1, day=20))
    indicator.update(make_candle(close="200", volume=10, minute=2, day=21))

    assert indicator.value() == Decimal("200")
