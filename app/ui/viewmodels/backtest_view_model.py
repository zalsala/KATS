"""Backtest view model."""

from __future__ import annotations

from app.ui.models.display_models import BacktestDisplayResult
from app.ui.viewmodels.base import ViewModelBase


class BacktestViewModel(ViewModelBase):
    """State for the backtest view."""

    def __init__(self) -> None:
        super().__init__()
        self.is_running: bool = False
        self.last_result: BacktestDisplayResult | None = None
        self.last_message: str = ""

    def set_running(self, running: bool) -> None:
        self.is_running = running
        self.notify("running")

    def set_result(self, result: BacktestDisplayResult | None, *, message: str = "") -> None:
        self.last_result = result
        self.last_message = message
        self.notify("result")
