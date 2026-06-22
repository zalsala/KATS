"""Chart view model."""

from __future__ import annotations

from app.chart.candle import Candle
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
    ) -> None:
        super().__init__()
        self._chart_service = chart_service
        self.symbol_code = symbol_code
        self.candles: list[Candle] = []

    def refresh(self) -> None:
        """Reload candles for the active symbol from ChartService."""
        self.candles = self._chart_service.get_candles(self.symbol_code)
        self.notify("candles")

    def set_symbol(self, symbol_code: str) -> None:
        """Change the active symbol and refresh candles."""
        self.symbol_code = symbol_code
        self.refresh()
