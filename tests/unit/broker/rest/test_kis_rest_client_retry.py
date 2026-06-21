"""Retry behavior tests for KisRestClient."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.rest_fixtures import (
    MockRestHttpTransport,
    _success_response,
    build_test_rest_client,
)

from app.broker.kis.exceptions.rest_exceptions import BrokerServerError
from app.broker.kis.rest.http_transport import RestHttpResponse

pytestmark = pytest.mark.unit


class TestKisRestClientRetry:
    """Tests for REST client retry behavior."""

    def test_get_retries_on_503_then_succeeds(self, tmp_path: Path) -> None:
        """GET retries transient HTTP 503 and eventually succeeds."""
        transport = MockRestHttpTransport()
        transport.queue(
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            _success_response(output={"value": "ok"}),
        )
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=3, backoff_factor=2)

        result = client.get("/uapi/test/v1/sample", "TEST0001")

        assert result.success is True
        assert result.output["value"] == "ok"
        assert transport.call_count == 2

    def test_get_retries_on_kis_rate_limit_code(self, tmp_path: Path) -> None:
        """GET retries when KIS returns EGW00201."""
        transport = MockRestHttpTransport()
        transport.queue(
            RestHttpResponse(
                status_code=200,
                body={"rt_cd": "1", "msg_cd": "EGW00201", "msg1": "rate limit"},
                text="{}",
                headers={},
            ),
            _success_response(),
        )
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=3)

        result = client.get("/uapi/test/v1/sample", "TEST0001")

        assert result.success is True
        assert transport.call_count == 2

    def test_get_stops_retry_after_max_attempts(self, tmp_path: Path) -> None:
        """GET returns failed result after retry budget is exhausted."""
        transport = MockRestHttpTransport()
        transport.queue(
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
        )
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=2)

        result = client.get("/uapi/test/v1/sample", "TEST0001", raise_on_error=False)

        assert result.success is False
        assert result.status_code == 503
        assert transport.call_count == 3

    def test_get_retries_on_network_error(self, tmp_path: Path) -> None:
        """GET retries transport network failures."""
        from app.broker.kis.exceptions.rest_exceptions import NetworkError

        transport = MockRestHttpTransport()
        transport.queue(NetworkError("connection reset"), _success_response())
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=3)

        result = client.get("/uapi/test/v1/sample", "TEST0001")

        assert result.success is True
        assert transport.call_count == 2

    def test_exhausted_retries_raise_server_error(self, tmp_path: Path) -> None:
        """Raising client converts final HTTP failure to mapped exception."""
        transport = MockRestHttpTransport()
        transport.queue(
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
            RestHttpResponse(status_code=503, body={"msg1": "busy"}, text="{}", headers={}),
        )
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=1)

        with pytest.raises(BrokerServerError):
            client.get("/uapi/test/v1/sample", "TEST0001")
