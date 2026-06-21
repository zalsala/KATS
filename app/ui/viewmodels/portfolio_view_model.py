"""Portfolio view model."""

from __future__ import annotations

from app.ui.models.display_models import PortfolioSummary, PositionRow
from app.ui.viewmodels.base import ViewModelBase


class PortfolioViewModel(ViewModelBase):
    """State for the portfolio view."""

    def __init__(self) -> None:
        super().__init__()
        self.summary: PortfolioSummary | None = None
        self.positions: list[PositionRow] = []

    def update(self, *, summary: PortfolioSummary | None, positions: list[PositionRow]) -> None:
        self.summary = summary
        self.positions = positions
        self.notify("portfolio")
