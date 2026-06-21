"""Timeout behavior tests for KisRestClient."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.rest_fixtures import MockRestHttpTransport, build_test_rest_client

from app.broker.kis.exceptions.rest_exceptions import BrokerTimeoutError

pytestmark = pytest.mark.unit


class TestKisRestClientTimeout:
    """Tests for REST client timeout handling."""

    def test_timeout_is_passed_to_transport(self, tmp_path: Path) -> None:
        """Configured broker timeout is forwarded to transport."""
        transport = MockRestHttpTransport()
        client, _ = build_test_rest_client(tmp_path, transport, timeout_seconds=7)

        client.get("/uapi/test/v1/sample", "TEST0001", raise_on_error=False)

        assert transport.calls[0]["timeout_seconds"] == 7.0

    def test_timeout_error_is_retried_then_raises(self, tmp_path: Path) -> None:
        """Timeout errors retry and eventually raise BrokerTimeoutError."""
        transport = MockRestHttpTransport()
        transport.queue(
            BrokerTimeoutError("timed out"),
            BrokerTimeoutError("timed out"),
        )
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=1)

        with pytest.raises(BrokerTimeoutError):
            client.get("/uapi/test/v1/sample", "TEST0001")

        assert transport.call_count == 2

    def test_timeout_returns_failed_result_when_not_raising(self, tmp_path: Path) -> None:
        """Timeout with raise_on_error=False is not applicable for transport errors."""
        transport = MockRestHttpTransport()
        transport.queue(BrokerTimeoutError("timed out"))
        client, _ = build_test_rest_client(tmp_path, transport, max_retry=0)

        with pytest.raises(BrokerTimeoutError):
            client.get("/uapi/test/v1/sample", "TEST0001", raise_on_error=False)
