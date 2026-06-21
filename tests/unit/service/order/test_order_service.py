"""OrderService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.order_fixtures import (
    build_test_order_service,
    sample_account_context,
    sample_order_cash_response,
    sample_order_rvsecncl_response,
)

from app.broker.kis.rest.api_result import ApiResult
from app.dto.order.order_requests import (
    CancelOrderRequest,
    CashBuyOrderRequest,
    CashSellOrderRequest,
    ModifyOrderRequest,
)
from app.service.order.order_service import OrderValidationError

pytestmark = pytest.mark.unit

ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"
ORDER_RVSECNL_PATH = "/uapi/domestic-stock/v1/trading/order-rvsecncl"


class TestOrderServiceSuccess:
    """Success path tests for OrderService."""

    def test_place_cash_buy_order(self) -> None:
        service, client, hashkey_manager = build_test_order_service(
            post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
        )
        account = sample_account_context()
        request = CashBuyOrderRequest(
            account=account,
            symbol_code="005930",
            quantity="1",
            price="70000",
        )

        result = service.place_cash_buy_order(request)

        assert result.success is True
        assert result.order_number == "0000123456"
        assert result.rt_cd == "0"
        assert len(service.orders) == 1
        assert service.orders[0].side == "buy"
        assert client.calls[0]["body"]["SLL_BUY_DVSN_CD"] == "02"
        assert client.calls[0]["hashkey"] == "mock-hash-key"
        assert len(hashkey_manager.calls) == 1

    def test_place_cash_sell_order(self) -> None:
        service, client, _ = build_test_order_service(
            post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
        )
        request = CashSellOrderRequest(
            account=sample_account_context(),
            symbol_code="005930",
            quantity="1",
            price="70000",
        )

        result = service.place_cash_sell_order(request)

        assert result.success is True
        assert client.calls[0]["body"]["SLL_BUY_DVSN_CD"] == "01"

    def test_modify_order(self) -> None:
        service, client, _ = build_test_order_service(
            post_responses_by_path={ORDER_RVSECNL_PATH: sample_order_rvsecncl_response()}
        )
        request = ModifyOrderRequest(
            account=sample_account_context(),
            order_branch="06010",
            original_order_number="0000123456",
            quantity="1",
            price="71000",
        )

        result = service.modify_order(request)

        assert result.order_number == "0000123457"
        assert client.calls[0]["tr_id"] == "TTTC0013U"
        assert client.calls[0]["body"]["RVSE_CNCL_DVSN_CD"] == "01"

    def test_cancel_order(self) -> None:
        service, client, _ = build_test_order_service(
            post_responses_by_path={ORDER_RVSECNL_PATH: sample_order_rvsecncl_response()}
        )
        request = CancelOrderRequest(
            account=sample_account_context(),
            order_branch="06010",
            original_order_number="0000123456",
        )

        result = service.cancel_order(request)

        assert result.success is True
        assert client.calls[0]["body"]["RVSE_CNCL_DVSN_CD"] == "02"


class TestOrderServiceValidation:
    """Validation tests for OrderService."""

    def test_rejects_empty_symbol(self) -> None:
        service, _, _ = build_test_order_service()
        request = CashBuyOrderRequest(
            account=sample_account_context(),
            symbol_code="",
            quantity="1",
            price="70000",
        )

        with pytest.raises(OrderValidationError, match="symbol_code"):
            service.place_cash_buy_order(request)

    def test_rejects_zero_quantity(self) -> None:
        service, _, _ = build_test_order_service()
        request = CashBuyOrderRequest(
            account=sample_account_context(),
            symbol_code="005930",
            quantity="0",
            price="70000",
        )

        with pytest.raises(OrderValidationError, match="quantity"):
            service.place_cash_buy_order(request)


class TestOrderServiceFailure:
    """Failure path tests using ErrorMapper."""

    def test_failed_order_raises_broker_api_error(self) -> None:
        from app.broker.kis.exceptions.rest_exceptions import BrokerApiError

        failed = ApiResult(
            success=False,
            status_code=200,
            data={"rt_cd": "1", "msg_cd": "APBK0013", "msg1": "주문거부"},
            rt_cd="1",
            msg_cd="APBK0013",
            msg1="주문거부",
            latency_ms=1.0,
            tr_id="TTTC0012U",
            path=ORDER_CASH_PATH,
            method="POST",
        )
        service, _, _ = build_test_order_service(post_error_by_path={ORDER_CASH_PATH: failed})
        request = CashBuyOrderRequest(
            account=sample_account_context(),
            symbol_code="005930",
            quantity="1",
            price="70000",
        )

        with pytest.raises(BrokerApiError, match="주문거부"):
            service.place_cash_buy_order(request)

        assert len(service.orders) == 0
