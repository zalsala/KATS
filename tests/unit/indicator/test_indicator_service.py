"""IndicatorService tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.unit.indicator.conftest import make_candle

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.indicator.ema_indicator import EmaIndicator
from app.indicator.indicator_service import IndicatorService
from app.indicator.sma_indicator import SmaIndicator
from app.indicator.vwap_indicator import VwapIndicator
from app.service.chart.chart_service import ChartService

pytestmark = pytest.mark.unit


def test_indicator_service_routing() -> None:
    service = IndicatorService()
    samsung_sma = SmaIndicator(2)
    hynix_sma = SmaIndicator(2)
    service.register_indicator("005930", "1m", "sma_2", samsung_sma)
    service.register_indicator("000660", "1m", "sma_2", hynix_sma)

    service.update_candle(make_candle(symbol="005930", close="100", minute=1))
    service.update_candle(make_candle(symbol="005930", close="200", minute=2))
    service.update_candle(make_candle(symbol="000660", close="300", minute=1))
    service.update_candle(make_candle(symbol="000660", close="500", minute=2))

    assert service.get_indicator_value("005930", "1m", "sma_2") == Decimal("150")
    assert service.get_indicator_value("000660", "1m", "sma_2") == Decimal("400")


def test_indicator_service_multiple_timeframes() -> None:
    service = IndicatorService()
    m1_sma = SmaIndicator(2)
    m5_sma = SmaIndicator(2)
    service.register_indicator("005930", "1m", "sma_2", m1_sma)
    service.register_indicator("005930", "5m", "sma_2", m5_sma)

    service.update_candle(make_candle(symbol="005930", interval="1m", close="100", minute=1))
    service.update_candle(make_candle(symbol="005930", interval="1m", close="200", minute=2))
    service.update_candle(make_candle(symbol="005930", interval="5m", close="300", minute=1))
    service.update_candle(make_candle(symbol="005930", interval="5m", close="500", minute=2))

    assert service.get_indicator_value("005930", "1m", "sma_2") == Decimal("150")
    assert service.get_indicator_value("005930", "5m", "sma_2") == Decimal("400")


def test_chart_service_updates_registered_indicators() -> None:
    indicators = IndicatorService()
    indicators.register_indicator(
        "005930",
        "1m",
        "sma_2",
        SmaIndicator(2),
        factory=lambda: SmaIndicator(2),
    )
    indicators.register_indicator("005930", "1m", "vwap", VwapIndicator())
    indicators.register_indicator("005930", "1m", "ema_2", EmaIndicator(2))

    chart = ChartService(store=InMemoryCandleStore(), indicator_service=indicators)
    base = datetime(2024, 6, 20, 12, 0, 0, tzinfo=UTC)

    chart.on_trade("005930", "100", 10, timestamp=base.replace(minute=1))
    chart.on_trade("005930", "200", 10, timestamp=base.replace(minute=2))

    assert indicators.get_indicator_value("005930", "1m", "sma_2") is None
    assert indicators.get_indicator_value("005930", "1m", "ema_2") is None
    assert indicators.get_indicator_value("005930", "1m", "vwap") == Decimal("100")

    chart.on_trade("005930", "300", 10, timestamp=base.replace(minute=3))
    assert indicators.get_indicator_value("005930", "1m", "sma_2") == Decimal("150")
    assert indicators.get_indicator_value("005930", "1m", "ema_2") == Decimal("150")
    assert indicators.get_indicator_value("005930", "1m", "vwap") == Decimal("150")
