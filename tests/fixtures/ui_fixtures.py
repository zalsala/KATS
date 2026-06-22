"""Shared fixtures for UI tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.domain.order.order import Order
from app.domain.order.order_result import OrderResult
from app.dto.order.order_requests import CashBuyOrderRequest, CashSellOrderRequest
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.service.backtest.backtest_service import build_backtest_service
from app.service.chart.chart_service import build_chart_service
from app.service.portfolio.portfolio_service import build_portfolio_service
from app.service.risk.risk_service import build_risk_service
from app.service.strategy.strategy_service import build_strategy_service
from app.ui.context.ui_app_context import UiAppContext
from app.ui.controllers.ui_controller import UiController
from app.ui.ui_session import UiSession
from app.ui.viewmodels.main_view_model import MainViewModel


class MockOrderService:
    """Mock order service for UI tests."""

    def __init__(self) -> None:
        self.last_request: CashBuyOrderRequest | CashSellOrderRequest | None = None

    def place_cash_buy_order(self, request: CashBuyOrderRequest) -> OrderResult:
        self.last_request = request
        return OrderResult(
            success=True,
            order_number="00001",
            order_branch="00001",
            order_time="120000",
            rt_cd="0",
            msg_cd="0000",
            msg1="mock buy ok",
            order=Order(
                order_number="00001",
                order_branch="00001",
                symbol_code=request.symbol_code,
                price=request.price,
                quantity=request.quantity,
                side="buy",
            ),
        )

    def place_cash_sell_order(self, request: CashSellOrderRequest) -> OrderResult:
        self.last_request = request
        return OrderResult(
            success=True,
            order_number="00002",
            order_branch="00001",
            order_time="120000",
            rt_cd="0",
            msg_cd="0000",
            msg1="mock sell ok",
            order=Order(
                order_number="00002",
                order_branch="00001",
                symbol_code=request.symbol_code,
                price=request.price,
                quantity=request.quantity,
                side="sell",
            ),
        )


def build_test_ui_context(*, order_service: MockOrderService | None = None) -> UiAppContext:
    """Build UI context without loading filesystem config."""
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    portfolio_service = build_portfolio_service(event_bus=event_bus, account_no="12345678")
    strategy_service = build_strategy_service(event_bus=event_bus)
    risk_service = build_risk_service(portfolio_service=portfolio_service, event_bus=event_bus)
    backtest_service = build_backtest_service()
    chart_service = build_chart_service()
    config_manager = MagicMock()
    settings = MagicMock()
    settings.environment = "test"
    settings.secrets.account_type = "mock"
    settings.secrets.account_no = "12345678"
    settings.config.application.version = "1.0.0"
    config_manager.load.return_value = settings
    return UiAppContext(
        config_manager=config_manager,
        event_bus=event_bus,
        portfolio_service=portfolio_service,
        strategy_service=strategy_service,
        risk_service=risk_service,
        backtest_service=backtest_service,
        chart_service=chart_service,
        order_service=order_service,
    )


def build_test_ui_session(*, order_service: MockOrderService | None = None) -> UiSession:
    """Build started UI session for tests."""
    context = build_test_ui_context(order_service=order_service)
    session = UiSession(context=context)
    session.start()
    return session


def build_test_main_view_model(*, chart_service=None) -> MainViewModel:
    from app.service.chart.chart_service import build_chart_service

    service = chart_service or build_chart_service()
    return MainViewModel(chart_service=service)


def build_test_ui_controller(*, order_service: MockOrderService | None = None) -> UiController:
    return UiController(context=build_test_ui_context(order_service=order_service))
