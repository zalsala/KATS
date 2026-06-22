"""Main window view model."""

from __future__ import annotations

from app.service.chart.chart_service import ChartService, build_chart_service
from app.ui.viewmodels.account_summary_view_model import AccountSummaryViewModel
from app.ui.viewmodels.backtest_view_model import BacktestViewModel
from app.ui.viewmodels.base import ViewModelBase
from app.ui.viewmodels.chart_view_model import ChartViewModel
from app.ui.viewmodels.dashboard_view_model import DashboardViewModel
from app.ui.viewmodels.log_view_model import LogViewModel
from app.ui.viewmodels.market_view_model import MarketViewModel
from app.ui.viewmodels.order_entry_view_model import OrderEntryViewModel
from app.ui.viewmodels.order_view_model import OrderViewModel
from app.ui.viewmodels.portfolio_view_model import PortfolioViewModel
from app.ui.viewmodels.position_view_model import PositionViewModel
from app.ui.viewmodels.settings_view_model import SettingsViewModel
from app.ui.viewmodels.strategy_view_model import StrategyViewModel
from app.ui.viewmodels.watchlist_view_model import WatchlistViewModel


class MainViewModel(ViewModelBase):
    """Aggregates child view models for the main window."""

    def __init__(self, *, chart_service: ChartService | None = None) -> None:
        super().__init__()
        self.active_view: str = "dashboard"
        self.status_message: str = "Ready"
        self.dashboard = DashboardViewModel()
        self.market = MarketViewModel()
        self.chart = ChartViewModel(chart_service or build_chart_service())
        self.order = OrderViewModel()
        self.order_entry = OrderEntryViewModel()
        self.position = PositionViewModel()
        self.account_summary = AccountSummaryViewModel()
        self.portfolio = PortfolioViewModel()
        self.strategy = StrategyViewModel()
        self.backtest = BacktestViewModel()
        self.log = LogViewModel()
        self.settings = SettingsViewModel()
        self.watchlist = WatchlistViewModel()

    def set_active_view(self, view_name: str) -> None:
        self.active_view = view_name
        self.notify("active_view")

    def set_status_message(self, message: str) -> None:
        self.status_message = message
        self.notify("status_message")
