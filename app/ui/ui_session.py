"""UI session wiring."""

from __future__ import annotations

from app.account.kis_domestic_account_summary_adapter import KISDomesticAccountSummaryAdapter
from app.account.kis_domestic_balance_adapter import KISDomesticBalanceAdapter
from app.order.kis_domestic_order_adapter import KISDomesticOrderAdapter
from app.repository.json.json_watchlist_repository import JsonWatchlistRepository
from app.service.trading.trading_service import TradingService
from app.service.watchlist.watchlist_service import WatchlistService
from app.ui.account_summary_event_bridge import AccountSummaryEventBridge
from app.ui.chart_event_bridge import ChartEventBridge
from app.ui.context.ui_app_context import UiAppContext
from app.ui.controllers.account_summary_controller import AccountSummaryController
from app.ui.controllers.order_entry_controller import OrderEntryController
from app.ui.controllers.position_controller import PositionController
from app.ui.controllers.ui_controller import UiController
from app.ui.controllers.ui_event_bridge import UiEventBridge
from app.ui.controllers.watchlist_controller import WatchlistController
from app.ui.position_event_bridge import PositionEventBridge
from app.ui.viewmodels.main_view_model import MainViewModel


class UiSession:
    """Wires services, controller, event bridge, and view models."""

    def __init__(self, *, context: UiAppContext) -> None:
        self.context = context
        self.view_model = MainViewModel(chart_service=context.chart_service)
        self.controller = UiController(context=context)
        self.watchlist_service = WatchlistService(
            repository=JsonWatchlistRepository.from_project_root(
                context.config_manager.project_root
            ),
            market_service=context.market_service,
        )
        self.watchlist_controller = WatchlistController(
            controller=self.controller,
            watchlist_service=self.watchlist_service,
            view_model=self.view_model,
        )
        order_adapter = (
            KISDomesticOrderAdapter(order_service=context.order_service)
            if context.order_service is not None
            else None
        )
        balance_adapter = (
            KISDomesticBalanceAdapter(account_service=context.account_service)
            if context.account_service is not None
            else None
        )
        account_summary_adapter = (
            KISDomesticAccountSummaryAdapter(account_service=context.account_service)
            if context.account_service is not None
            else None
        )
        self.trading_service = TradingService(
            order_service=context.order_service,
            config_manager=context.config_manager,
            adapter=order_adapter,
            balance_adapter=balance_adapter,
            account_summary_adapter=account_summary_adapter,
        )
        self.order_entry_controller = OrderEntryController(
            trading_service=self.trading_service,
            view_model=self.view_model,
        )
        self.position_controller = PositionController(
            trading_service=self.trading_service,
            view_model=self.view_model,
        )
        self.account_summary_controller = AccountSummaryController(
            trading_service=self.trading_service,
            view_model=self.view_model,
        )
        self.event_bridge = UiEventBridge(
            controller=self.controller,
            view_model=self.view_model,
            watchlist_controller=self.watchlist_controller,
        )
        self.chart_event_bridge = ChartEventBridge(chart_view_model=self.view_model.chart)
        self.position_event_bridge = PositionEventBridge(
            position_controller=self.position_controller,
        )
        self.account_summary_event_bridge = AccountSummaryEventBridge(
            account_summary_controller=self.account_summary_controller,
        )
        self._started = False

    def start(self) -> None:
        """Start services and UI event subscriptions."""
        if self._started:
            return
        self.context.start()
        self.watchlist_controller.initialize()
        self.order_entry_controller.initialize()
        self.position_controller.initialize()
        self.account_summary_controller.initialize()
        self.event_bridge.register(self.context.event_bus)
        self.chart_event_bridge.register(self.context.event_bus)
        self.position_event_bridge.register(self.context.event_bus)
        self.account_summary_event_bridge.register(self.context.event_bus)
        self.event_bridge.refresh_all()
        self._started = True

    def stop(self) -> None:
        """Stop UI subscriptions and services."""
        if not self._started:
            return
        self.watchlist_controller.shutdown()
        self.account_summary_event_bridge.unregister(self.context.event_bus)
        self.position_event_bridge.unregister(self.context.event_bus)
        self.chart_event_bridge.unregister(self.context.event_bus)
        self.event_bridge.unregister(self.context.event_bus)
        self.context.stop()
        self._started = False
