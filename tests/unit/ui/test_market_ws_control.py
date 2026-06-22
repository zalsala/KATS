"""Market view websocket control tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_market_view_has_ws_controls(qapp) -> None:
    view_model = MainViewModel()
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)
    view.show()
    qapp.processEvents()

    assert view._symbol_input is not None  # noqa: SLF001
    assert view._connect_button is not None  # noqa: SLF001
    assert view._subscribe_button is not None  # noqa: SLF001


def test_connect_button_calls_controller(qapp) -> None:
    view_model = MainViewModel()
    controller = MagicMock(spec=UiController)
    controller.connect_websocket.return_value = None
    view = MarketView(view_model=view_model, controller=controller)

    view._connect_button.click()  # noqa: SLF001
    qapp.processEvents()

    controller.connect_websocket.assert_called_once()
    assert view_model.market.websocket_connected is True


def test_subscribe_button_calls_controller_and_blocks_empty_symbol(qapp) -> None:
    view_model = MainViewModel()
    controller = MagicMock(spec=UiController)
    view = MarketView(view_model=view_model, controller=controller)

    view._symbol_input.setText("")  # noqa: SLF001
    view._subscribe_button.click()  # noqa: SLF001
    qapp.processEvents()

    controller.subscribe_realtime_price.assert_not_called()
    assert "required" in view_model.market.status_message.lower()

    view._symbol_input.setText("005930")  # noqa: SLF001
    view._subscribe_button.click()  # noqa: SLF001
    qapp.processEvents()

    controller.subscribe_realtime_price.assert_called_with("005930")
    assert "005930" in view_model.market.subscribed_symbols


def test_disconnect_button_calls_controller(qapp) -> None:
    view_model = MainViewModel()
    controller = MagicMock(spec=UiController)
    controller.disconnect_websocket.return_value = None
    view = MarketView(view_model=view_model, controller=controller)

    view_model.market.set_websocket_connected(True)
    view._disconnect_button.click()  # noqa: SLF001
    qapp.processEvents()

    controller.disconnect_websocket.assert_called_once()
    assert view_model.market.websocket_connected is False
