"""Unit tests for ResponseParser."""

from __future__ import annotations

import pytest

from app.broker.kis.rest.http_transport import RestHttpResponse
from app.broker.kis.rest.response_parser import ResponseParser

pytestmark = pytest.mark.unit


class TestResponseParser:
    """Tests for ResponseParser."""

    def test_parse_success_response(self) -> None:
        """Successful KIS response is parsed with rt_cd 0."""
        response = RestHttpResponse(
            status_code=200,
            body={
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다.",
                "output": {"stck_prpr": "70000"},
            },
            text="{}",
            headers={},
        )

        result = ResponseParser().parse(
            response,
            method="GET",
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            latency_ms=12.5,
        )

        assert result.success is True
        assert result.rt_cd == "0"
        assert result.output["stck_prpr"] == "70000"
        assert result.latency_ms == 12.5

    def test_parse_api_failure(self) -> None:
        """Non-zero rt_cd marks result as failed."""
        response = RestHttpResponse(
            status_code=200,
            body={"rt_cd": "1", "msg_cd": "ERROR", "msg1": "invalid input"},
            text="{}",
            headers={},
        )

        result = ResponseParser().parse(
            response,
            method="POST",
            path="/uapi/test",
            tr_id="TEST0001",
            latency_ms=3.0,
        )

        assert result.success is False
        assert result.msg_cd == "ERROR"

    def test_parse_http_error_body(self) -> None:
        """Non-200 HTTP status marks result as failed."""
        response = RestHttpResponse(
            status_code=500,
            body={"msg1": "server error"},
            text="{}",
            headers={},
        )

        result = ResponseParser().parse(
            response,
            method="GET",
            path="/uapi/test",
            tr_id="TEST0001",
            latency_ms=1.0,
        )

        assert result.success is False
        assert result.status_code == 500
