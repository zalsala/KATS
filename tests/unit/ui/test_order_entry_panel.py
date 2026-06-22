"""Order entry panel tests."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication
from tests.fixtures.auth_fixtures import make_kats_config
from tests.fixtures.order_fixtures import (
    build_test_order_service,
    sample_order_cash_rejected_response,
    sample_order_cash_response,
)

from app.config.secret_manager import KisSecrets
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL
from app.order.kis_domestic_order_adapter import KISDomesticOrderAdapter
from app.service.trading.trading_service import TradingService
from app.ui.controllers.order_entry_controller import OrderEntryController
from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.order_entry_panel import OrderEntryPanel

pytestmark = pytest.mark.unit

ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"


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
    order_service=None,
) -> tuple[OrderEntryController, MainViewModel, TradingService]:
    service, _, _ = build_test_order_service(
        post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
    )
    resolved_service = order_service or service
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
        order_service=resolved_service,
        config_manager=config_manager,
        adapter=KISDomesticOrderAdapter(order_service=resolved_service),
    )
    view_model = MainViewModel()
    controller = OrderEntryController(
        trading_service=trading_service,
        view_model=view_model,
    )
    controller.initialize()
    return controller, view_model, trading_service


def test_initial_panel_state(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = OrderEntryPanel(view_model=view_model.order_entry, controller=controller)
    panel.show()
    qapp.processEvents()

    assert view_model.order_entry.side == "buy"
    assert view_model.order_entry.order_type == "limit"
    assert view_model.order_entry.trading_enabled is True


def test_selected_symbol_sync_from_watchlist(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.watchlist.set_selected_symbol("000660")
    controller.sync_symbol("000660")

    assert view_model.order_entry.symbol_code == "000660"


def test_buy_limit_order_validation(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("70000")

    assert controller.validate() == []


def test_sell_limit_order_validation(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_side("sell")
    view_model.order_entry.set_quantity("2")
    view_model.order_entry.set_price("71000")

    assert controller.validate() == []


def test_market_order_price_handling(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = OrderEntryPanel(view_model=view_model.order_entry, controller=controller)
    panel.show()
    qapp.processEvents()

    panel._order_type.setCurrentText("market")  # noqa: SLF001
    qapp.processEvents()

    assert view_model.order_entry.price == "0"
    assert panel._price.isEnabled() is False  # noqa: SLF001
    assert view_model.order_entry.estimated_amount() is None


def test_invalid_quantity_blocked(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("0")
    view_model.order_entry.set_price("70000")

    assert controller.submit() is False
    assert view_model.order_entry.error_message


def test_invalid_price_blocked(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("0")

    assert controller.submit() is False
    assert view_model.order_entry.error_message


def test_trading_disabled_when_not_configured(qapp) -> None:
    view_model = MainViewModel()
    config_manager = MagicMock()
    trading_service = TradingService(
        order_service=None,
        config_manager=config_manager,
        adapter=None,
    )
    controller = OrderEntryController(
        trading_service=trading_service,
        view_model=view_model,
    )
    controller.initialize()
    panel = OrderEntryPanel(view_model=view_model.order_entry, controller=controller)
    panel.show()
    qapp.processEvents()

    assert view_model.order_entry.trading_enabled is False
    assert controller.submit() is False


def test_successful_vts_order_flow(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("70000")

    assert controller.submit() is True
    assert view_model.order_entry.last_success is True
    assert view_model.order_entry.result_message


def test_failed_order_response_displayed(qapp) -> None:
    service, _, _ = build_test_order_service(
        post_responses_by_path={
            ORDER_CASH_PATH: sample_order_cash_rejected_response(msg1="Rejected")
        }
    )
    controller, view_model, _ = _build_controller(order_service=service)
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("70000")

    assert controller.submit() is False
    assert view_model.order_entry.error_message == "Rejected"


def test_real_trading_guard_blocks_submit(qapp) -> None:
    controller, view_model, _ = _build_controller(
        account_type=KIS_ACCOUNT_REAL,
        live_trading_enabled=False,
    )
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("70000")

    assert controller.submit() is False
    assert "Real trading is disabled" in view_model.order_entry.error_message


def test_market_view_embeds_order_entry_panel(qapp) -> None:
    controller, view_model, _ = _build_controller()
    ui_controller = UiController(context=MagicMock())
    view = MarketView(
        view_model=view_model,
        controller=ui_controller,
        order_entry_controller=controller,
    )
    view.show()
    qapp.processEvents()

    assert isinstance(view.order_entry_panel, OrderEntryPanel)


def test_no_sensitive_values_logged(qapp, caplog) -> None:
    controller, view_model, _ = _build_controller()
    view_model.order_entry.sync_symbol("005930")
    view_model.order_entry.set_quantity("1")
    view_model.order_entry.set_price("70000")

    with caplog.at_level(logging.INFO):
        controller.submit()

    joined = " ".join(record.message for record in caplog.records)
    assert "12345678" not in joined
    assert "app-secret" not in joined
