"""Repository tests for KisAccountRepository."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.account_fixtures import (
    build_test_account_repository,
    sample_account_context,
    sample_balance_response,
    sample_psbl_order_response,
    sample_trade_history_response,
)

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.account_api_keys import (
    INQUIRE_BALANCE,
)
from app.repository.kis.account_api_client import AccountApiClient
from app.repository.kis.account_api_resolver import build_account_api_resolver

pytestmark = pytest.mark.unit

BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"
PSBL_PATH = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
CCLD_PATH = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"


class TestKisAccountRepository:
    """Tests for KisAccountRepository."""

    def test_get_account_balance_uses_registry_tr_id(self) -> None:
        repository, client = build_test_account_repository(
            {BALANCE_PATH: sample_balance_response()}
        )

        balance = repository.get_account_balance(sample_account_context())

        assert balance.total_evaluation_amount == Decimal("10000000")
        assert client.calls[0]["tr_id"] == "TTTC8434R"
        assert client.calls[0]["path"] == BALANCE_PATH
        assert client.calls[0]["params"]["CANO"] == "12345678"

    def test_get_deposit_from_balance_api(self) -> None:
        repository, _ = build_test_account_repository({BALANCE_PATH: sample_balance_response()})

        deposit = repository.get_deposit(sample_account_context())

        assert deposit.total_deposit_amount == Decimal("2000000")

    def test_get_holding_stocks_from_balance_output1(self) -> None:
        repository, _ = build_test_account_repository({BALANCE_PATH: sample_balance_response()})

        holdings = repository.get_holding_stocks(sample_account_context())

        assert len(holdings) == 1
        assert holdings[0].stock_name == "삼성전자"

    def test_get_orderable_amount(self) -> None:
        repository, client = build_test_account_repository(
            {PSBL_PATH: sample_psbl_order_response()}
        )

        orderable = repository.get_orderable_amount(
            sample_account_context(),
            symbol_code="005930",
        )

        assert orderable.max_buy_amount == Decimal("1500000")
        assert client.calls[0]["tr_id"] == "TTTC8908R"

    def test_get_trade_history(self) -> None:
        repository, client = build_test_account_repository(
            {CCLD_PATH: sample_trade_history_response()}
        )

        history = repository.get_trade_history(
            sample_account_context(),
            start_date="20260601",
            end_date="20260620",
        )

        assert len(history) == 1
        assert client.calls[0]["tr_id"] == "TTTC0081R"

    def test_account_api_client_resolves_registry_only(self) -> None:
        """AccountApiClient must resolve TR ID via ApiRegistry."""
        from tests.fixtures.account_fixtures import MockAccountRestClient

        rest_client = MockAccountRestClient(
            responses_by_path={BALANCE_PATH: sample_balance_response()}
        )
        resolver = build_account_api_resolver(ApiRegistry.default(), use_mock_tr_id=False)
        client = AccountApiClient(rest_client=rest_client, api_resolver=resolver)

        metadata = ApiRegistry.default().endpoints.get_by_key(INQUIRE_BALANCE)
        assert metadata is not None
        client.get(INQUIRE_BALANCE, sample_account_context().to_base_params())

        assert rest_client.calls[0]["tr_id"] == metadata.tr_id
