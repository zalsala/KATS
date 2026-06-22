"""Shared fixtures for order tests."""

from __future__ import annotations

from typing import Any

from app.broker.kis.api import ApiRegistry
from app.broker.kis.rest.api_result import ApiResult
from app.domain.account.value_objects.account_context import AccountContext
from app.order.kis_order_api_client import KisOrderApiClient
from app.service.order.order_service import OrderService


class MockHashKeyManager:
    """Mock HashKey manager returning a fixed hash value."""

    def __init__(self, *, hash_value: str = "mock-hash-key") -> None:
        self.hash_value = hash_value
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        body: dict[str, Any],
        *,
        tr_id: str | None = None,
    ) -> str:
        self.calls.append({"body": body, "tr_id": tr_id})
        return self.hash_value


class MockOrderRestClient:
    """Mock REST client for order POST tests."""

    def __init__(
        self,
        *,
        post_responses_by_path: dict[str, dict[str, Any]] | None = None,
        post_error_by_path: dict[str, ApiResult] | None = None,
    ) -> None:
        self._post_responses = post_responses_by_path or {}
        self._post_errors = post_error_by_path or {}
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        *,
        raise_on_error: bool = True,
    ) -> ApiResult:
        _ = (path, tr_id, params, raise_on_error)
        return ApiResult(
            success=True,
            status_code=200,
            data={"rt_cd": "0"},
            rt_cd="0",
            msg_cd="",
            msg1="",
            latency_ms=1.0,
        )

    def post(
        self,
        path: str,
        tr_id: str,
        body: dict[str, Any] | None = None,
        *,
        hashkey: str | None = None,
        raise_on_error: bool = True,
    ) -> ApiResult:
        self.calls.append(
            {"method": "POST", "path": path, "tr_id": tr_id, "body": body, "hashkey": hashkey}
        )
        error = self._post_errors.get(path)
        if error is not None:
            if raise_on_error and not error.success:
                from app.broker.kis.rest.error_mapper import ErrorMapper

                ErrorMapper().raise_for_result(error)
            return error

        payload = self._post_responses.get(path, {})
        rt_cd = str(payload.get("rt_cd", "0"))
        msg_cd = str(payload.get("msg_cd", "MCA00000"))
        msg1 = str(payload.get("msg1", "ok"))
        return ApiResult(
            success=rt_cd == "0",
            status_code=200,
            data={
                "rt_cd": rt_cd,
                "msg_cd": msg_cd,
                "msg1": msg1,
                "output": payload.get("output", {}),
            },
            rt_cd=rt_cd,
            msg_cd=msg_cd,
            msg1=msg1,
            latency_ms=1.0,
            tr_id=tr_id,
            path=path,
            method="POST",
        )


def sample_account_context() -> AccountContext:
    return AccountContext(account_no="12345678", account_product="01")


def sample_order_cash_response() -> dict[str, Any]:
    return {
        "output": {
            "KRX_FWDG_ORD_ORGNO": "06010",
            "ODNO": "0000123456",
            "ORD_TMD": "093000",
        }
    }


def sample_order_cash_rejected_response(*, msg1: str = "Rejected") -> dict[str, Any]:
    """Build a rejected order-cash mock response payload."""
    return {
        "rt_cd": "1",
        "msg_cd": "APBK0013",
        "msg1": msg1,
        "output": {},
    }


def sample_order_rvsecncl_response() -> dict[str, Any]:
    return {
        "output": {
            "KRX_FWDG_ORD_ORGNO": "06010",
            "ODNO": "0000123457",
            "ORD_TMD": "100000",
        }
    }


def build_test_order_service(
    *,
    post_responses_by_path: dict[str, dict[str, Any]] | None = None,
    post_error_by_path: dict[str, ApiResult] | None = None,
    use_mock_tr_id: bool = False,
) -> tuple[OrderService, MockOrderRestClient, MockHashKeyManager]:
    """Build OrderService with mock REST client and HashKey manager."""
    rest_client = MockOrderRestClient(
        post_responses_by_path=post_responses_by_path,
        post_error_by_path=post_error_by_path,
    )
    hashkey_manager = MockHashKeyManager()
    api_client = KisOrderApiClient(
        rest_client=rest_client,
        registry=ApiRegistry.default(),
        hashkey_manager=hashkey_manager,
        use_mock_tr_id=use_mock_tr_id,
    )
    service = OrderService(order_api_client=api_client)
    return service, rest_client, hashkey_manager
