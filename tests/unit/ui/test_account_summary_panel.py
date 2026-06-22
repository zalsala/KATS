"""Account summary panel tests."""

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

from app.account.kis_domestic_account_summary_adapter import KISDomesticAccountSummaryAdapter
from app.account.kis_domestic_balance_adapter import KISDomesticBalanceAdapter
from app.config.secret_manager import KisSecrets
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL
from app.domain.position.position_item import PositionItem
from app.events.base_event import BaseEvent
from app.events.event_types import EventType
from app.service.account.account_service import build_account_service
from app.service.trading.trading_service import TradingService
from app.ui.account_summary_event_bridge import AccountSummaryEventBridge
from app.ui.controllers.account_summary_controller import AccountSummaryController
from app.ui.controllers.ui_controller import UiController
from app.ui.formatting.account_formatting import format_signed_currency
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.account_summary_panel import AccountSummaryPanel

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
) -> tuple[AccountSummaryController, MainViewModel, TradingService]:
    repository, _ = build_test_account_repository({BALANCE_PATH: sample_balance_response()})
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
        account_summary_adapter=KISDomesticAccountSummaryAdapter(account_service=account_service),
    )
    view_model = MainViewModel()
    controller = AccountSummaryController(
        trading_service=trading_service,
        view_model=view_model,
    )
    controller.initialize()
    return controller, view_model, trading_service


def test_initial_empty_state_when_unconfigured(qapp) -> None:
    view_model = MainViewModel()
    trading_service = TradingService(
        order_service=None,
        config_manager=MagicMock(),
        adapter=None,
        balance_adapter=None,
        account_summary_adapter=None,
    )
    controller = AccountSummaryController(
        trading_service=trading_service,
        view_model=view_model,
    )
    controller.initialize()
    panel = AccountSummaryPanel(
        view_model=view_model.account_summary,
        controller=controller,
    )
    panel.show()
    qapp.processEvents()

    assert view_model.account_summary.summary is None
    assert view_model.account_summary.error_message


def test_successful_vts_summary_load(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = AccountSummaryPanel(view_model=view_model.account_summary, controller=controller)
    panel.show()
    qapp.processEvents()

    assert view_model.account_summary.summary is not None
    assert view_model.account_summary.summary.cash_balance == Decimal("2000000")
    assert panel._cash_balance.text() == "2,000,000"  # noqa: SLF001


def test_failed_summary_load_displays_error(qapp) -> None:
    controller, view_model, trading_service = _build_controller()
    trading_service.get_account_summary = MagicMock(side_effect=RuntimeError("network failure"))
    panel = AccountSummaryPanel(view_model=view_model.account_summary, controller=controller)
    panel.show()
    qapp.processEvents()

    assert controller.refresh() is False
    assert view_model.account_summary.error_message == "Failed to load account summary"


def test_real_account_lookup_blocked(qapp) -> None:
    controller, view_model, _ = _build_controller(
        account_type=KIS_ACCOUNT_REAL,
        live_trading_enabled=False,
    )
    panel = AccountSummaryPanel(view_model=view_model.account_summary, controller=controller)
    panel.show()
    qapp.processEvents()

    assert controller.refresh() is False
    assert "Real account lookup is disabled" in view_model.account_summary.error_message


def test_refresh_button_calls_controller(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = AccountSummaryPanel(view_model=view_model.account_summary, controller=controller)
    panel.show()
    qapp.processEvents()

    view_model.account_summary.set_summary(None)
    panel._refresh_button.click()  # noqa: SLF001
    qapp.processEvents()

    assert view_model.account_summary.summary is not None


def test_currency_and_profit_loss_formatting_in_panel(qapp) -> None:
    controller, view_model, _ = _build_controller()
    panel = AccountSummaryPanel(view_model=view_model.account_summary, controller=controller)
    panel.show()
    qapp.processEvents()

    summary = view_model.account_summary.summary
    assert summary is not None
    assert panel._total_pl.text() == format_signed_currency(
        summary.total_profit_loss_amount
    )  # noqa: SLF001


def test_realtime_valuation_update_from_held_symbol_tick(qapp) -> None:
    controller, view_model, _ = _build_controller()
    view_model.position.set_positions(
        [
            PositionItem(
                symbol_code="005930",
                stock_name="삼성전자",
                quantity=Decimal("10"),
                average_price=Decimal("70000"),
                current_price=Decimal("75000"),
                evaluation_amount=Decimal("750000"),
                profit_loss_amount=Decimal("50000"),
                profit_loss_rate=Decimal("7.14"),
            )
        ]
    )
    bridge = AccountSummaryEventBridge(account_summary_controller=controller)
    event = BaseEvent(
        event_type=EventType.MARKET_DATA,
        source="test",
        payload={"symbol_code": "005930", "price": "80000"},
    )

    bridge._handle_market_data(event)  # noqa: SLF001

    summary = view_model.account_summary.summary
    assert summary is not None
    assert summary.total_evaluation_amount == Decimal("2800000")


def test_market_view_embeds_account_summary_panel(qapp) -> None:
    controller, view_model, _ = _build_controller()
    ui_controller = UiController(context=MagicMock())
    view = MarketView(
        view_model=view_model,
        controller=ui_controller,
        account_summary_controller=controller,
    )
    view.show()
    qapp.processEvents()

    assert isinstance(view.account_summary_panel, AccountSummaryPanel)


def test_no_sensitive_values_logged(qapp, caplog) -> None:
    controller, view_model, _ = _build_controller()

    with caplog.at_level(logging.INFO):
        controller.refresh()

    joined = " ".join(record.message for record in caplog.records)
    assert "12345678" not in joined
    assert "app-secret" not in joined
