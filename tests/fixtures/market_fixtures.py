"""Shared fixtures for market domain tests."""

from __future__ import annotations

from typing import Any

from app.broker.kis.rest.api_result import ApiResult


class MockRestClient:
    """Mock REST client implementing the RestClient protocol."""

    def __init__(
        self,
        *,
        output: dict[str, Any] | None = None,
        output_by_path: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize mock responses."""
        self._output = output or {}
        self._output_by_path = output_by_path or {}
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        *,
        raise_on_error: bool = True,
    ) -> ApiResult:
        """Record and return a canned GET response."""
        _ = raise_on_error
        self.calls.append({"method": "GET", "path": path, "tr_id": tr_id, "params": params})
        payload = self._output_by_path.get(path, self._output)
        return ApiResult(
            success=True,
            status_code=200,
            data={"rt_cd": "0", "msg_cd": "MCA00000", "msg1": "ok", "output": payload},
            rt_cd="0",
            msg_cd="MCA00000",
            msg1="ok",
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
        """Record POST call and return empty success."""
        _ = (body, hashkey, raise_on_error)
        self.calls.append({"method": "POST", "path": path, "tr_id": tr_id})
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


def sample_price_output() -> dict[str, str]:
    """Return sample KIS inquire-price output."""
    return {
        "mksc_shrn_iscd": "005930",
        "hts_kor_isnm": "삼성전자",
        "stck_prpr": "70000",
        "prdy_vrss": "500",
        "prdy_ctrt": "0.72",
    }


def sample_asking_output() -> dict[str, str]:
    """Return sample KIS inquire-asking-price output."""
    return {
        "mksc_shrn_iscd": "005930",
        "hts_kor_isnm": "삼성전자",
        "bidp1": "69900",
        "askp1": "70000",
        "bidp_rsqn1": "100",
        "askp_rsqn1": "200",
        "bidp2": "69800",
        "askp2": "70100",
        "bidp_rsqn2": "50",
        "askp_rsqn2": "80",
    }
