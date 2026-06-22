"""Chart view model."""

from __future__ import annotations

from app.chart.candle import Candle
from app.chart.timeframe import DEFAULT_TIMEFRAME, Timeframe, resolve_timeframe
from app.indicator.indicator_series import IndicatorSeriesMap
from app.indicator.indicator_service import (
    DEFAULT_VWAP_NAME,
    ema_indicator_name,
    sma_indicator_name,
)
from app.service.chart.chart_service import ChartService
from app.ui.models.indicator_settings import IndicatorSettings
from app.ui.viewmodels.base import ViewModelBase

DEFAULT_SYMBOL = "005930"


class ChartViewModel(ViewModelBase):
    """State for the candle chart view."""

    def __init__(
        self,
        chart_service: ChartService,
        *,
        symbol_code: str = DEFAULT_SYMBOL,
        selected_timeframe: Timeframe | str = DEFAULT_TIMEFRAME,
    ) -> None:
        super().__init__()
        self._chart_service = chart_service
        self.symbol_code = symbol_code
        self.selected_timeframe = resolve_timeframe(selected_timeframe)
        self.candles: list[Candle] = []
        self.indicator_series: IndicatorSeriesMap = {}
        self.indicator_settings = IndicatorSettings()
        self.total_ticks_received = 0
        self.total_candles = 0
        self.last_trade_time = ""
        self.last_trade_price = ""
        self.last_trade_symbol = ""

    def refresh(self) -> None:
        """Reload candles and diagnostics for the active symbol and timeframe."""
        self.candles = self._chart_service.get_candles(
            self.symbol_code,
            self.selected_timeframe,
        )
        stats = self._chart_service.get_chart_stats(
            self.symbol_code,
            self.selected_timeframe,
        )
        self.total_ticks_received = int(stats["ticks"])
        self.total_candles = int(stats["candles"])
        self.last_trade_time = str(stats["last_trade_time"])
        self.last_trade_price = str(stats["last_price"])
        self.last_trade_symbol = str(stats["last_symbol"])
        self.refresh_indicators()
        self.notify("candles")

    def refresh_indicators(self) -> None:
        """Reload indicator overlay series for the active symbol and timeframe."""
        indicator_service = self._chart_service.indicator_service
        if indicator_service is None or not self.candles:
            self.indicator_series = {}
            self.notify("indicators")
            return

        settings = self.indicator_settings
        timeframe = self.selected_timeframe.value
        enabled_names = indicator_service.configure_overlay_indicators(
            self.symbol_code,
            timeframe,
            sma_enabled=settings.sma_enabled,
            sma_period=settings.sma_period,
            ema_enabled=settings.ema_enabled,
            ema_period=settings.ema_period,
            vwap_enabled=settings.vwap_enabled,
        )
        self.indicator_series = indicator_service.build_overlay_series(
            self.symbol_code,
            timeframe,
            self.candles,
            names=enabled_names,
        )
        self.notify("indicators")

    def update_indicator_settings(self, settings: IndicatorSettings) -> None:
        """Apply indicator overlay settings and refresh overlay data."""
        settings.validate()
        self.indicator_settings = settings
        self.refresh_indicators()

    def set_symbol(self, symbol_code: str) -> None:
        """Change the active symbol and refresh candles."""
        self.symbol_code = symbol_code
        self.refresh()

    def set_timeframe(self, timeframe: Timeframe | str) -> None:
        """Change the active timeframe and refresh candles."""
        self.selected_timeframe = resolve_timeframe(timeframe)
        self.notify("timeframe")
        self.refresh()

    def enabled_indicator_names(self) -> tuple[str, ...]:
        """Return overlay series names enabled by the current settings."""
        settings = self.indicator_settings
        names: list[str] = []
        if settings.sma_enabled:
            names.append(sma_indicator_name(settings.sma_period))
        if settings.ema_enabled:
            names.append(ema_indicator_name(settings.ema_period))
        if settings.vwap_enabled:
            names.append(DEFAULT_VWAP_NAME)
        return tuple(names)
