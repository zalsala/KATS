"""EventBus UI update tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.ui_fixtures import build_test_main_view_model, build_test_ui_controller

from app.events.domain_events import MarketDataEvent, PortfolioEvent
from app.ui.controllers.ui_event_bridge import UiEventBridge

pytestmark = pytest.mark.unit


def test_event_bridge_updates_market_view_model() -> None:
    controller = build_test_ui_controller()
    view_model = build_test_main_view_model()
    bridge = UiEventBridge(controller=controller, view_model=view_model)
    bridge.register(controller.context.event_bus)

    controller.context.event_bus.publish(
        MarketDataEvent(
            source="test",
            payload={"symbol_code": "005930", "price": "71000"},
        )
    )

    assert view_model.market.symbol_code == "005930"
    assert view_model.market.current_price == Decimal("71000")


def test_event_bridge_refresh_on_portfolio_event() -> None:
    controller = build_test_ui_controller()
    view_model = build_test_main_view_model()
    bridge = UiEventBridge(controller=controller, view_model=view_model)
    bridge.register(controller.context.event_bus)

    controller.context.portfolio_service.apply_account(
        {
            "account_no": "12345678",
            "total_deposit": "1000000",
            "orderable_cash": "1000000",
            "holdings": [],
        }
    )
    controller.context.event_bus.publish(
        PortfolioEvent(source="portfolio_engine", payload={"reason": "account_sync"})
    )

    assert view_model.portfolio.summary is not None
    assert len(view_model.log.entries) >= 1
