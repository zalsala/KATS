"""Mock REST integration tests for KisRestClient."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.rest_fixtures import (
    MockRestHttpTransport,
    _success_response,
    build_test_rest_client,
)

from app.broker.kis.exceptions.rest_exceptions import BrokerApiError
from app.broker.kis.rest.http_transport import RestHttpResponse

pytestmark = pytest.mark.unit


class TestMockRestClient:
    """End-to-end REST client tests with mock transport."""

    def test_get_returns_parsed_result(self, tmp_path: Path) -> None:
        """GET request returns successful ApiResult."""
        transport = MockRestHttpTransport(
            default_response=_success_response(output={"stck_prpr": "65000"})
        )
        client, _ = build_test_rest_client(tmp_path, transport)

        result = client.get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            params={"FID_INPUT_ISCD": "005930"},
        )

        assert result.success is True
        assert result.output["stck_prpr"] == "65000"
        assert transport.call_count == 1
        assert transport.calls[0]["method"] == "GET"
        assert "FID_INPUT_ISCD=005930" in transport.calls[0]["url"]

    def test_post_returns_parsed_result(self, tmp_path: Path) -> None:
        """POST request sends JSON body and parses response."""
        transport = MockRestHttpTransport(default_response=_success_response())
        client, _ = build_test_rest_client(tmp_path, transport)

        result = client.post(
            "/uapi/test/v1/sample",
            "TEST0001",
            body={"sample": "value"},
            raise_on_error=False,
        )

        assert result.success is True
        assert transport.calls[0]["method"] == "POST"
        assert transport.calls[0]["body"] == {"sample": "value"}

    def test_authenticated_headers_are_sent(self, tmp_path: Path) -> None:
        """REST requests include bearer token and app credentials."""
        transport = MockRestHttpTransport(default_response=_success_response())
        client, _ = build_test_rest_client(tmp_path, transport)

        client.get("/uapi/test/v1/sample", "TEST0001")

        headers = transport.calls[0]["headers"]
        assert headers["authorization"].startswith("Bearer ")
        assert headers["appkey"] == "test-app-key"
        assert headers["appsecret"] == "test-app-secret"
        assert headers["tr_id"] == "TEST0001"

    def test_raise_on_error_false_returns_failed_result(self, tmp_path: Path) -> None:
        """Failed API result can be returned without raising."""
        transport = MockRestHttpTransport(
            default_response=RestHttpResponse(
                status_code=200,
                body={"rt_cd": "1", "msg_cd": "ERR", "msg1": "bad request"},
                text="{}",
                headers={},
            )
        )
        client, _ = build_test_rest_client(tmp_path, transport)

        result = client.get("/uapi/test/v1/sample", "TEST0001", raise_on_error=False)

        assert result.success is False
        assert result.msg_cd == "ERR"

    def test_raise_on_error_true_raises_mapped_exception(self, tmp_path: Path) -> None:
        """Failed API result raises BrokerApiError by default."""
        transport = MockRestHttpTransport(
            default_response=RestHttpResponse(
                status_code=200,
                body={"rt_cd": "1", "msg_cd": "ERR", "msg1": "bad request"},
                text="{}",
                headers={},
            )
        )
        client, _ = build_test_rest_client(tmp_path, transport)

        with pytest.raises(BrokerApiError):
            client.get("/uapi/test/v1/sample", "TEST0001")
