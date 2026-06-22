"""Trading service account summary tests."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from tests.fixtures.account_fixtures import (
    build_test_account_repository,
    sample_balance_response,
)
from tests.fixtures.auth_fixtures import make_kats_config

from app.account.kis_domestic_account_summary_adapter import KISDomesticAccountSummaryAdapter
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
) -> TradingService:
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
    return TradingService(
        order_service=None,
        config_manager=config_manager,
        adapter=None,
        balance_adapter=None,
        account_summary_adapter=KISDomesticAccountSummaryAdapter(account_service=account_service),
    )


def test_vts_account_summary_load() -> None:
    trading = _build_trading_service()
    summary = trading.get_account_summary()

    assert summary.cash_balance == Decimal("2000000")
    assert summary.available_buying_power == Decimal("1500000")
    assert summary.total_evaluation_amount == Decimal("10000000")
    assert summary.total_profit_loss_amount == Decimal("1000000")


def test_real_account_summary_blocked_by_default() -> None:
    trading = _build_trading_service(account_type=KIS_ACCOUNT_REAL, live_trading_enabled=False)

    with pytest.raises(TradingNotAllowedError, match="Real account lookup is disabled"):
        trading.get_account_summary()
