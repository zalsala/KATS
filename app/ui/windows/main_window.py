"""Main application window."""

from __future__ import annotations

from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar, QWidget

from app.ui.ui_session import UiSession
from app.ui.views.backtest_view import BacktestView
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.log_view import LogView
from app.ui.views.market_view import MarketView
from app.ui.views.order_view import OrderView
from app.ui.views.portfolio_view import PortfolioView
from app.ui.views.settings_view import SettingsView
from app.ui.views.strategy_view import StrategyView
from app.ui.widgets.status_bar import KatsStatusBar


class MainWindow(QMainWindow):
    """Primary KATS desktop window."""

    def __init__(self, *, session: UiSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._vm = session.view_model
        self.setWindowTitle("KATS - Korea Investment Auto Trading System")
        self.resize(1200, 800)

        self._stack = QStackedWidget()
        self._views: dict[str, QWidget] = {
            "dashboard": DashboardView(view_model=self._vm),
            "market": MarketView(
                view_model=self._vm,
                controller=session.controller,
                watchlist_controller=session.watchlist_controller,
                order_entry_controller=session.order_entry_controller,
                position_controller=session.position_controller,
                account_summary_controller=session.account_summary_controller,
            ),
            "order": OrderView(view_model=self._vm, controller=session.controller),
            "portfolio": PortfolioView(view_model=self._vm),
            "strategy": StrategyView(view_model=self._vm, controller=session.controller),
            "backtest": BacktestView(view_model=self._vm, controller=session.controller),
            "log": LogView(view_model=self._vm),
            "settings": SettingsView(view_model=self._vm),
        }
        for widget in self._views.values():
            self._stack.addWidget(widget)

        self.setCentralWidget(self._stack)
        self._build_toolbar()
        self._status_bar = KatsStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._bind_view_model()
        self._show_view("dashboard")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Navigation", self)
        self.addToolBar(toolbar)
        for key, label in [
            ("dashboard", "Dashboard"),
            ("market", "Market"),
            ("order", "Order"),
            ("portfolio", "Portfolio"),
            ("strategy", "Strategy"),
            ("backtest", "Backtest"),
            ("log", "Logs"),
            ("settings", "Settings"),
        ]:
            action = QAction(label, self)
            action.triggered.connect(lambda _checked=False, view=key: self._show_view(view))
            toolbar.addAction(action)

        emergency = QAction("Emergency Stop", self)
        emergency.triggered.connect(self._on_emergency_stop)
        toolbar.addAction(emergency)

    def _show_view(self, view_name: str) -> None:
        widget = self._views.get(view_name)
        if widget is None:
            return
        self._stack.setCurrentWidget(widget)
        self._vm.set_active_view(view_name)

    def _on_emergency_stop(self) -> None:
        self._session.controller.activate_emergency_stop()
        self._session.event_bridge.refresh_all()
        self._vm.set_status_message("Emergency stop activated")

    def _bind_view_model(self) -> None:
        self._vm.dashboard.add_listener(lambda _field: self._refresh_status_bar())
        self._vm.add_listener(lambda _field: self._refresh_status_bar())
        self._refresh_status_bar()

    def _refresh_status_bar(self) -> None:
        dashboard = self._vm.dashboard
        self._status_bar.update_connection(dashboard.connection_status)
        self._status_bar.update_emergency_stop(dashboard.emergency_stop)
        self._status_bar.update_message(self._vm.status_message)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._session.stop()
        super().closeEvent(event)
