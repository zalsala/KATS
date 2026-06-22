"""Chart view model."""

from __future__ import annotations

from app.chart.candle import Candle
from app.chart.timeframe import DEFAULT_TIMEFRAME, Timeframe, resolve_timeframe
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
        self.notify("candles")

    def set_symbol(self, symbol_code: str) -> None:
        """Change the active symbol and refresh candles."""
        self.symbol_code = symbol_code
        self.refresh()

    def set_timeframe(self, timeframe: Timeframe | str) -> None:
        """Change the active timeframe and refresh candles."""
        self.selected_timeframe = resolve_timeframe(timeframe)
        self.notify("timeframe")
        self.refresh()
