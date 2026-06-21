"""Dashboard view model."""

from __future__ import annotations

from app.ui.models.display_models import PortfolioSummary
from app.ui.viewmodels.base import ViewModelBase


class DashboardViewModel(ViewModelBase):
    """State for the dashboard view."""

    def __init__(self) -> None:
        super().__init__()
        self.connection_status: str = "Disconnected"
        self.emergency_stop: bool = False
        self.running_strategy_count: int = 0
        self.summary: PortfolioSummary | None = None

    def update_connection_status(self, status: str) -> None:
        self.connection_status = status
        self.notify("connection_status")

    def update_emergency_stop(self, active: bool) -> None:
        self.emergency_stop = active
        self.notify("emergency_stop")

    def update_running_strategy_count(self, count: int) -> None:
        self.running_strategy_count = count
        self.notify("running_strategy_count")

    def update_summary(self, summary: PortfolioSummary | None) -> None:
        self.summary = summary
        self.notify("summary")
