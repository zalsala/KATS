"""Shared fixtures for account domain tests."""

from __future__ import annotations

from typing import Any

from app.broker.kis.api import ApiRegistry
from app.broker.kis.rest.api_result import ApiResult
from app.domain.account.value_objects.account_context import AccountContext
from app.repository.kis.account_api_client import AccountApiClient
from app.repository.kis.account_api_resolver import build_account_api_resolver
from app.repository.kis.kis_account_repository import KisAccountRepository


class MockAccountRestClient:
    """Mock REST client with output and output1 support."""

    def __init__(
        self,
        *,
        responses_by_path: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._responses_by_path = responses_by_path or {}
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        *,
        raise_on_error: bool = True,
    ) -> ApiResult:
        _ = raise_on_error
        self.calls.append({"method": "GET", "path": path, "tr_id": tr_id, "params": params})
        payload = self._responses_by_path.get(path, {})
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
                "output1": payload.get("output1", []),
            },
            rt_cd=rt_cd,
            msg_cd=msg_cd,
            msg1=msg1,
            latency_ms=1.0,
            tr_id=tr_id,
            path=path,
            method="GET",
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
        _ = (body, hashkey, raise_on_error, path, tr_id)
        return ApiResult(
            success=True,
            status_code=200,
            data={"rt_cd": "0"},
            rt_cd="0",
            msg_cd="",
            msg1="",
            latency_ms=1.0,
            tr_id=tr_id,
            path=path,
            method="POST",
        )


def sample_account_context() -> AccountContext:
    return AccountContext(account_no="12345678", account_product="01")


def sample_balance_response() -> dict[str, Any]:
    return {
        "output": {
            "tot_evlu_amt": "10000000",
            "pchs_amt_smtl_amt": "9000000",
            "evlu_pfls_smtl_amt": "1000000",
            "evlu_pfls_rt": "11.11",
            "dnca_tot_amt": "2000000",
            "ord_psbl_cash": "1500000",
            "nxdy_excc_amt": "1800000",
        },
        "output1": [
            {
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "hldg_qty": "10",
                "pchs_avg_pric": "70000",
                "prpr": "75000",
                "evlu_amt": "750000",
                "evlu_pfls_amt": "50000",
                "evlu_pfls_rt": "7.14",
            }
        ],
    }


def sample_psbl_order_response() -> dict[str, Any]:
    return {
        "output": {
            "pdno": "005930",
            "ord_psbl_cash": "1500000",
            "max_buy_qty": "20",
            "max_buy_amt": "1500000",
        }
    }


def sample_trade_history_response() -> dict[str, Any]:
    return {
        "output1": [
            {
                "ord_dt": "20260620",
                "ord_tmd": "093000",
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "sll_buy_dvsn_cd": "02",
                "tot_ccld_qty": "1",
                "avg_prvs": "70000",
                "tot_ccld_amt": "70000",
                "odno": "00001234",
            }
        ]
    }


def sample_balance_rejected_response(*, msg1: str = "Balance lookup failed") -> dict[str, Any]:
    """Build a rejected balance inquiry mock response payload."""
    return {
        "rt_cd": "1",
        "msg_cd": "EGW00123",
        "msg1": msg1,
        "output": {},
        "output1": [],
    }


def build_test_account_repository(
    responses_by_path: dict[str, dict[str, Any]],
    *,
    use_mock_tr_id: bool = False,
) -> tuple[KisAccountRepository, MockAccountRestClient]:
    """Build account repository with mock REST client."""
    rest_client = MockAccountRestClient(responses_by_path=responses_by_path)
    api_client = AccountApiClient(
        rest_client=rest_client,
        api_resolver=build_account_api_resolver(
            ApiRegistry.default(), use_mock_tr_id=use_mock_tr_id
        ),
    )
    repository = KisAccountRepository(account_api_client=api_client)
    return repository, rest_client
