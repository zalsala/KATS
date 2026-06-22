"""Trading service position lookup tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from tests.fixtures.account_fixtures import (
    build_test_account_repository,
    sample_balance_response,
)
from tests.fixtures.auth_fixtures import make_kats_config

from app.account.kis_domestic_balance_adapter import KISDomesticBalanceAdapter
from app.config.secret_manager import KisSecrets
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL
from app.service.account.account_service import build_account_service
from app.service.trading.trading_service import TradingNotAllowedError, TradingService

pytestmark = pytest.mark.unit

BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"


def _build_trading_service(
    *,
    account_type: str = KIS_ACCOUNT_MOCK,
    live_trading_enabled: bool = False,
    balance_response: dict | None = None,
) -> TradingService:
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
    return TradingService(
        order_service=None,
        config_manager=config_manager,
        adapter=None,
        balance_adapter=KISDomesticBalanceAdapter(account_service=account_service),
    )


def test_vts_position_load_uses_adapter() -> None:
    trading = _build_trading_service()
    positions = trading.get_positions()

    assert len(positions) == 1
    assert positions[0].symbol_code == "005930"
    assert positions[0].stock_name == "삼성전자"


def test_real_account_lookup_blocked_by_default() -> None:
    trading = _build_trading_service(account_type=KIS_ACCOUNT_REAL, live_trading_enabled=False)

    with pytest.raises(TradingNotAllowedError, match="Real account lookup is disabled"):
        trading.get_positions()


def test_position_lookup_unavailable_without_adapter() -> None:
    trading = TradingService(
        order_service=None,
        config_manager=MagicMock(),
        adapter=None,
        balance_adapter=None,
    )

    assert trading.is_position_lookup_available() is False
