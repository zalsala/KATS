"""Position panel tests."""

from __future__ import annotations

import logging
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication
from tests.fixtures.account_fixtures import (
    build_test_account_repository,
    sample_balance_response,
)
from tests.fixtures.auth_fixtures import make_kats_config

from app.account.kis_domestic_balance_adapter import KISDomesticBalanceAdapter
from app.config.secret_manager import KisSecrets
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL
from app.events.base_event import BaseEvent
from app.events.event_types import EventType
from app.service.account.account_service import build_account_service
from app.service.trading.trading_service import TradingService
from app.ui.controllers.position_controller import PositionController
from app.ui.controllers.ui_controller import UiController
from app.ui.position_event_bridge import PositionEventBridge
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.position_panel import PositionPanel

pytestmark = pytest.mark.unit

BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _build_controller(
    *,
    live_trading_enabled: bool = False,
    account_type: str = KIS_ACCOUNT_MOCK,
    balance_response: dict | None = None,
) -> tuple[PositionController, MainViewModel, TradingService]:
    repository, _ = build_test_account_repository(
        {BALANCE_PATH: balance_response or sample_balance_response()}
    )
    account_service = build_account_service(account_repository=repository)
    config_manager = MagicMock()
    settings = MagicMock()
    settings.secrets = KisSecrets(
        app_key="app-key",
        app_secret="app-secret",
        account_no="12345678",
        account_type=account_type,
    )
    settings.config = make_kats_config().model_copy(
        update={
            "order": make_kats_config().order.model_copy(
                update={"live_trading_enabled": live_trading_enabled}
            )
        }
    )
    config_manager.load.return_value = settings
    trading_service = TradingService(
        order_service=None,
        config_manager=config_manager,
        adapter=None,
        balance_adapter=KISDomesticBalanceAdapter(account_service=account_service),
    )
    view_model = MainViewModel()
    controller = PositionController(
        trading_service=trading_service,
        view_model=view_model,
    )
    controller.initialize()
    return controller, view_model, trading_service


def test_empty_position_panel_state(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.position.set_positions([])
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    assert view_model.position.positions == []
    assert panel._empty_label.isVisible()  # noqa: SLF001


def test_successful_vts_position_load(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    assert controller.refresh() is True
    qapp.processEvents()

    assert len(view_model.position.positions) == 1
    assert view_model.position.positions[0].symbol_code == "005930"
    assert panel._table.isVisible()  # noqa: SLF001


def test_failed_position_load_displays_error(qapp) -> None:
    controller, view_model, trading_service = _build_controller()
    trading_service.get_positions = MagicMock(side_effect=RuntimeError("network failure"))
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    assert controller.refresh() is False
    qapp.processEvents()

    assert view_model.position.positions == []
    assert view_model.position.error_message == "Failed to load positions"


def test_selected_symbol_highlight(qapp) -> None:
    controller, view_model, _ = _build_controller()
    controller.refresh()
    controller.sync_selected_symbol("005930")
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    assert view_model.position.selected_symbol == "005930"
    panel._table.highlight_symbol("005930")  # noqa: SLF001


def test_refresh_button_triggers_controller(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    view_model.position.set_positions([])
    panel._refresh_button.click()  # noqa: SLF001
    qapp.processEvents()

    assert len(view_model.position.positions) == 1


def test_realtime_tick_updates_current_price(qapp) -> None:
    controller, view_model, _ = _build_controller()
    controller.refresh()
    bridge = PositionEventBridge(position_controller=controller)
    event = BaseEvent(
        event_type=EventType.MARKET_DATA,
        source="test",
        event_name="market.tick",
        payload={"symbol_code": "005930", "price": "80000"},
    )

    bridge._handle_market_data(event)  # noqa: SLF001

    position = view_model.position.positions[0]
    assert position.current_price == Decimal("80000")
    assert position.evaluation_amount == Decimal("800000")


def test_real_account_lookup_blocked(qapp) -> None:
    controller, view_model, _ = _build_controller(
        account_type=KIS_ACCOUNT_REAL,
        live_trading_enabled=False,
    )
    panel = PositionPanel(view_model=view_model.position, controller=controller)
    panel.show()
    qapp.processEvents()

    assert controller.refresh() is False
    assert "Real account lookup is disabled" in view_model.position.error_message


def test_market_view_embeds_position_panel(qapp) -> None:
    controller, view_model, _ = _build_controller()
    ui_controller = UiController(context=MagicMock())
    view = MarketView(
        view_model=view_model,
        controller=ui_controller,
        position_controller=controller,
    )
    view.show()
    qapp.processEvents()

    assert isinstance(view.position_panel, PositionPanel)


def test_no_sensitive_values_logged(qapp, caplog) -> None:
    controller, view_model, _ = _build_controller()

    with caplog.at_level(logging.INFO):
        controller.refresh()

    joined = " ".join(record.message for record in caplog.records)
    assert "12345678" not in joined
    assert "app-secret" not in joined
