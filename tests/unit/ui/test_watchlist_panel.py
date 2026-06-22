"""Watchlist panel and interaction tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol
from app.repository.interfaces.market_repository import IMarketRepository
from app.repository.json.json_watchlist_repository import JsonWatchlistRepository
from app.service.watchlist.watchlist_service import WatchlistService
from app.ui.controllers.ui_controller import UiController
from app.ui.controllers.watchlist_controller import WatchlistController
from app.ui.models.watchlist_item import WatchlistItem
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.watchlist_panel import WatchlistPanel

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class FakeMarketRepository:
    """Market repository used for watchlist validation tests."""

    def __init__(self, *, names: dict[str, str] | None = None) -> None:
        self._names = names or {
            "005930": "Samsung Electronics",
            "000660": "SK Hynix",
        }

    def get_current_price(self, symbol: Symbol) -> StockPrice:
        if symbol.code not in self._names:
            msg = f"Unknown symbol: {symbol.code}"
            raise KeyError(msg)
        return StockPrice(
            symbol=symbol,
            stock_name=self._names[symbol.code],
            current_price=Decimal("81500"),
            change_amount=Decimal("1000"),
            change_rate=Decimal("1.24"),
            queried_at=datetime.now(UTC),
        )

    def get_asking_price(self, symbol: Symbol):  # noqa: ANN201
        raise NotImplementedError


def _build_controller(
    tmp_path: Path,
    *,
    market_repository: IMarketRepository | None = None,
) -> tuple[WatchlistController, MainViewModel, MagicMock]:
    from app.service.market.market_service import MarketService

    repository = JsonWatchlistRepository(tmp_path / "watchlist.json")
    market_service = (
        MarketService(market_repository=market_repository) if market_repository else None
    )
    service = WatchlistService(repository=repository, market_service=market_service)
    view_model = MainViewModel()
    ui_controller = MagicMock(spec=UiController)
    controller = WatchlistController(
        controller=ui_controller,
        watchlist_service=service,
        view_model=view_model,
    )
    return controller, view_model, ui_controller


def test_add_symbol(tmp_path) -> None:
    controller, view_model, _ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()

    assert controller.add_symbol("000660") is True
    assert any(item.symbol_code == "000660" for item in view_model.watchlist.items)
    assert view_model.watchlist.get_item("000660").name == "SK Hynix"  # type: ignore[union-attr]


def test_duplicate_prevention(tmp_path) -> None:
    controller, view_model, _ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()

    assert controller.add_symbol("005930") is False
    assert "already" in view_model.watchlist.error_message.lower()


def test_remove_symbol_and_auto_select(tmp_path) -> None:
    controller, view_model, ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()
    controller.add_symbol("000660")
    controller.select_symbol("000660")

    assert controller.remove_selected() is True
    assert view_model.watchlist.selected_symbol == "005930"
    assert not any(item.symbol_code == "000660" for item in view_model.watchlist.items)
    ui.unsubscribe_realtime_price.assert_called()


def test_symbol_selection_switches_subscription_and_chart(tmp_path) -> None:
    controller, view_model, ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()
    controller.add_symbol("000660")

    controller.select_symbol("000660")

    assert controller.active_subscription == "000660"
    assert view_model.chart.symbol_code == "000660"
    assert view_model.market.symbol_input == "000660"
    ui.subscribe_realtime_price.assert_called_with("000660")


def test_persistence_save_and_load(tmp_path) -> None:
    repository = JsonWatchlistRepository(tmp_path / "watchlist.json")
    service = WatchlistService(
        repository=repository,
        market_service=None,
    )
    service.save_state(
        items=(
            WatchlistItem(symbol_code="005930", name="Samsung Electronics"),
            WatchlistItem(symbol_code="000660", name="SK Hynix"),
        ),
        selected_symbol="000660",
    )

    loaded_items = service.load_items()
    assert len(loaded_items) == 2
    assert service.load_selected_symbol() == "000660"


def test_realtime_row_update(tmp_path) -> None:
    controller, view_model, _ui = _build_controller(tmp_path, market_repository=None)
    controller.initialize()
    controller.handle_market_tick(symbol_code="005930", price=Decimal("82000"))

    item = view_model.watchlist.get_item("005930")
    assert item is not None
    assert item.last_price == Decimal("82000")
    assert item.is_live is True


def test_subscription_switching_releases_previous_symbol(tmp_path) -> None:
    controller, view_model, ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()
    controller.add_symbol("000660")

    ui.reset_mock()
    controller.select_symbol("005930")

    ui.unsubscribe_realtime_price.assert_called_with("000660")
    ui.subscribe_realtime_price.assert_called_with("005930")
    assert controller.active_subscription == "005930"
    assert view_model.watchlist.get_item("005930").is_live is True  # type: ignore[union-attr]


def test_empty_watchlist_clears_chart(tmp_path) -> None:
    controller, view_model, ui = _build_controller(tmp_path, market_repository=None)
    view_model.watchlist.set_items([WatchlistItem(symbol_code="005930", name="Samsung")])
    view_model.watchlist.set_selected_symbol("005930")
    controller._active_subscription = "005930"  # noqa: SLF001

    assert controller.remove_selected() is True
    assert view_model.watchlist.items == []
    assert view_model.watchlist.selected_symbol is None
    assert view_model.chart.candles == []
    ui.unsubscribe_realtime_price.assert_called_with("005930")


def test_invalid_symbol_shows_error(tmp_path) -> None:
    controller, view_model, _ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()

    assert controller.add_symbol("ABC") is False
    assert view_model.watchlist.error_message


def test_market_view_embeds_watchlist_panel(qapp, tmp_path) -> None:
    controller, view_model, ui = _build_controller(
        tmp_path,
        market_repository=FakeMarketRepository(),
    )
    controller.initialize()
    view = MarketView(
        view_model=view_model,
        controller=ui,
        watchlist_controller=controller,
    )
    view.show()
    qapp.processEvents()

    assert isinstance(view.watchlist_panel, WatchlistPanel)
    assert view.watchlist_panel is not None
    assert view.watchlist_panel._table.rowCount() >= 1  # noqa: SLF001
