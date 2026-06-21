"""Tests for KisOrderApiClient."""

from __future__ import annotations

import pytest
from tests.fixtures.order_fixtures import (
    MockHashKeyManager,
    MockOrderRestClient,
    sample_account_context,
    sample_order_cash_response,
)

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.order_api_keys import ORDER_CASH
from app.order.kis_order_api_client import KisOrderApiClient

pytestmark = pytest.mark.unit

ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"


class TestKisOrderApiClient:
    """Tests for KisOrderApiClient."""

    def test_post_uses_registry_tr_id_and_hashkey(self) -> None:
        rest_client = MockOrderRestClient(
            post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
        )
        hashkey_manager = MockHashKeyManager()
        client = KisOrderApiClient(
            rest_client=rest_client,
            registry=ApiRegistry.default(),
            hashkey_manager=hashkey_manager,
            use_mock_tr_id=False,
        )

        client.post(ORDER_CASH, sample_account_context().to_base_params())

        assert rest_client.calls[0]["tr_id"] == "TTTC0012U"
        assert rest_client.calls[0]["hashkey"] == "mock-hash-key"
        assert len(hashkey_manager.calls) == 1

    def test_post_resolves_path_from_registry(self) -> None:
        rest_client = MockOrderRestClient(
            post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
        )
        client = KisOrderApiClient(
            rest_client=rest_client,
            registry=ApiRegistry.default(),
            hashkey_manager=MockHashKeyManager(),
            use_mock_tr_id=False,
        )

        client.post(ORDER_CASH, {})

        assert rest_client.calls[0]["path"] == ORDER_CASH_PATH
