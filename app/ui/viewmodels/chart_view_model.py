"""Chart view model."""

from __future__ import annotations

from app.chart.candle import Candle
from app.chart.timeframe import DEFAULT_TIMEFRAME, Timeframe, resolve_timeframe
from app.indicator.indicator_series import IndicatorSeriesMap
from app.indicator.indicator_service import DEFAULT_EMA_NAME, DEFAULT_SMA_NAME, DEFAULT_VWAP_NAME
from app.service.chart.chart_service import ChartService
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
        self.show_sma = True
        self.show_ema = False
        self.show_vwap = False
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

        timeframe = self.selected_timeframe.value
        indicator_service.ensure_default_indicators(self.symbol_code, timeframe)
        enabled_names = self._enabled_indicator_names()
        all_series = indicator_service.build_overlay_series(
            self.symbol_code,
            timeframe,
            self.candles,
            names=enabled_names,
        )
        self.indicator_series = all_series
        self.notify("indicators")

    def set_symbol(self, symbol_code: str) -> None:
        """Change the active symbol and refresh candles."""
        self.symbol_code = symbol_code
        self.refresh()

    def set_timeframe(self, timeframe: Timeframe | str) -> None:
        """Change the active timeframe and refresh candles."""
        self.selected_timeframe = resolve_timeframe(timeframe)
        self.notify("timeframe")
        self.refresh()

    def set_show_sma(self, enabled: bool) -> None:
        self.show_sma = enabled
        self.refresh_indicators()

    def set_show_ema(self, enabled: bool) -> None:
        self.show_ema = enabled
        self.refresh_indicators()

    def set_show_vwap(self, enabled: bool) -> None:
        self.show_vwap = enabled
        self.refresh_indicators()

    def _enabled_indicator_names(self) -> tuple[str, ...]:
        names: list[str] = []
        if self.show_sma:
            names.append(DEFAULT_SMA_NAME)
        if self.show_ema:
            names.append(DEFAULT_EMA_NAME)
        if self.show_vwap:
            names.append(DEFAULT_VWAP_NAME)
        return tuple(names)
