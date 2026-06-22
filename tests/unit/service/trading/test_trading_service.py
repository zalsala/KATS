"""Trading service tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from tests.fixtures.auth_fixtures import make_kats_config
from tests.fixtures.order_fixtures import build_test_order_service, sample_order_cash_response

from app.config.secret_manager import KisSecrets
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL
from app.dto.order.order_entry_request import OrderEntryRequest
from app.order.kis_domestic_order_adapter import KISDomesticOrderAdapter
from app.service.trading.trading_service import TradingNotAllowedError, TradingService

pytestmark = pytest.mark.unit

ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"


def _build_trading_service(
    *,
    account_type: str = KIS_ACCOUNT_MOCK,
    live_trading_enabled: bool = False,
    order_service=None,
) -> TradingService:
    service, _, _ = build_test_order_service(
        post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
    )
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
    resolved_service = order_service or service
    return TradingService(
        order_service=resolved_service,
        config_manager=config_manager,
        adapter=KISDomesticOrderAdapter(order_service=resolved_service),
    )


def test_buy_limit_order_validation_passes() -> None:
    trading = _build_trading_service()
    request = OrderEntryRequest(
        symbol_code="005930",
        side="buy",
        order_type="limit",
        quantity="1",
        price="70000",
    )

    assert trading.validate(request) == []


def test_sell_limit_order_validation_passes() -> None:
    trading = _build_trading_service()
    request = OrderEntryRequest(
        symbol_code="005930",
        side="sell",
        order_type="limit",
        quantity="2",
        price="71000",
    )

    assert trading.validate(request) == []


def test_market_order_requires_zero_price() -> None:
    trading = _build_trading_service()
    request = OrderEntryRequest(
        symbol_code="005930",
        side="buy",
        order_type="market",
        quantity="1",
        price="70000",
    )

    assert "Market order price must be 0" in trading.validate(request)


def test_invalid_quantity_blocked() -> None:
    trading = _build_trading_service()
    request = OrderEntryRequest(
        symbol_code="005930",
        side="buy",
        order_type="limit",
        quantity="0",
        price="70000",
    )

    assert trading.validate(request)


def test_invalid_price_blocked() -> None:
    trading = _build_trading_service()
    request = OrderEntryRequest(
        symbol_code="005930",
        side="buy",
        order_type="limit",
        quantity="1",
        price="0",
    )

    assert trading.validate(request)


def test_real_trading_blocked_without_explicit_enable() -> None:
    trading = _build_trading_service(account_type=KIS_ACCOUNT_REAL, live_trading_enabled=False)

    with pytest.raises(TradingNotAllowedError, match="Real trading is disabled"):
        trading.place_order(
            OrderEntryRequest(
                symbol_code="005930",
                side="buy",
                order_type="limit",
                quantity="1",
                price="70000",
            )
        )


def test_vts_order_flow_uses_adapter() -> None:
    trading = _build_trading_service()
    result = trading.place_order(
        OrderEntryRequest(
            symbol_code="005930",
            side="buy",
            order_type="limit",
            quantity="1",
            price="70000",
        )
    )

    assert result.success is True
    assert result.order_number == "0000123456"


def test_trading_disabled_when_order_service_missing() -> None:
    config_manager = MagicMock()
    trading = TradingService(
        order_service=None,
        config_manager=config_manager,
        adapter=None,
    )

    assert trading.is_trading_available() is False
