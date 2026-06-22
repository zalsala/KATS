"""Indicator settings UI tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication, QSpinBox

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.indicator.indicator_service import (
    IndicatorService,
    ema_indicator_name,
    sma_indicator_name,
)
from app.service.chart.chart_service import build_chart_service
from app.ui.controllers.ui_controller import UiController
from app.ui.models.indicator_settings import IndicatorSettings
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL, ChartViewModel
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _seed_candles(service, count: int = 25) -> None:
    for minute in range(1, count + 1):
        service.on_trade(
            DEFAULT_SYMBOL,
            str(100 + minute),
            10,
            timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        )


def test_indicator_settings_defaults() -> None:
    settings = IndicatorSettings()

    assert settings.sma_enabled is True
    assert settings.sma_period == 20
    assert settings.ema_enabled is False
    assert settings.ema_period == 20
    assert settings.vwap_enabled is False
    settings.validate()


def test_sma_period_update_rebuilds_overlay() -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()
    assert sma_indicator_name(20) in view_model.indicator_series

    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=True, sma_period=50),
    )

    assert sma_indicator_name(50) in view_model.indicator_series
    assert sma_indicator_name(20) not in view_model.indicator_series
    assert view_model.indicator_settings.sma_period == 50


def test_ema_period_update_rebuilds_overlay() -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()
    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=False, ema_enabled=True, ema_period=9),
    )

    assert ema_indicator_name(9) in view_model.indicator_series
    assert sma_indicator_name(20) not in view_model.indicator_series

    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=False, ema_enabled=True, ema_period=20),
    )

    assert ema_indicator_name(20) in view_model.indicator_series
    assert ema_indicator_name(9) not in view_model.indicator_series


def test_toggle_indicator_visibility() -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()
    assert sma_indicator_name(20) in view_model.indicator_series

    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=False, vwap_enabled=True),
    )
    assert sma_indicator_name(20) not in view_model.indicator_series
    assert "VWAP" in view_model.indicator_series


def test_chart_view_model_rebuild_on_settings_change() -> None:
    indicators = IndicatorService()
    service = build_chart_service(store=InMemoryCandleStore(), indicator_service=indicators)
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()

    names_before = indicators.list_indicator_names(DEFAULT_SYMBOL, "1m")
    assert sma_indicator_name(20) in names_before

    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=True, sma_period=60),
    )

    names_after = indicators.list_indicator_names(DEFAULT_SYMBOL, "1m")
    assert sma_indicator_name(60) in names_after
    assert sma_indicator_name(20) not in names_after
    assert sma_indicator_name(60) in view_model.indicator_series


def test_market_view_indicator_controls_exist(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    view_model = MainViewModel(chart_service=service)
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)

    assert isinstance(view._sma_period, QSpinBox)  # noqa: SLF001
    assert isinstance(view._ema_period, QSpinBox)  # noqa: SLF001
    assert view._sma_period.minimum() == IndicatorSettings.MIN_PERIOD  # noqa: SLF001
    assert view._sma_period.maximum() == IndicatorSettings.MAX_PERIOD  # noqa: SLF001
    assert view._ema_period.minimum() == IndicatorSettings.MIN_PERIOD  # noqa: SLF001
    assert view._ema_period.maximum() == IndicatorSettings.MAX_PERIOD  # noqa: SLF001


def test_invalid_period_values_rejected() -> None:
    with pytest.raises(ValueError, match="SMA period"):
        IndicatorSettings(sma_period=0).validate()

    with pytest.raises(ValueError, match="SMA period"):
        IndicatorSettings(sma_period=501).validate()

    with pytest.raises(ValueError, match="EMA period"):
        IndicatorSettings(ema_period=0).validate()

    with pytest.raises(ValueError, match="EMA period"):
        IndicatorSettings(ema_period=501).validate()

    view_model = ChartViewModel(
        build_chart_service(store=InMemoryCandleStore()),
        symbol_code=DEFAULT_SYMBOL,
    )
    with pytest.raises(ValueError):
        view_model.update_indicator_settings(IndicatorSettings(sma_period=0))

    assert IndicatorSettings.clamp_period(0) == IndicatorSettings.MIN_PERIOD
    assert IndicatorSettings.clamp_period(999) == IndicatorSettings.MAX_PERIOD
