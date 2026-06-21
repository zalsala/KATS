"""Strategy view model."""

from __future__ import annotations

from app.ui.models.display_models import StrategyRow
from app.ui.viewmodels.base import ViewModelBase


class StrategyViewModel(ViewModelBase):
    """State for the strategy view."""

    def __init__(self) -> None:
        super().__init__()
        self.strategies: list[StrategyRow] = []
        self.last_message: str = ""

    def update_strategies(self, strategies: list[StrategyRow]) -> None:
        self.strategies = strategies
        self.notify("strategies")

    def set_message(self, message: str) -> None:
        self.last_message = message
        self.notify("message")
