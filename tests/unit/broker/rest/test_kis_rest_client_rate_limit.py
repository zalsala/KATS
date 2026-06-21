"""Rate limit integration tests for KisRestClient."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.rest_fixtures import (
    MockRestHttpTransport,
    _success_response,
    build_test_rest_client,
)

from app.broker.kis.rest.kis_rest_client import KisRestClient
from app.broker.kis.rest.rate_limiter import RateLimiter

pytestmark = pytest.mark.unit


class TestKisRestClientRateLimit:
    """Tests for REST client rate limiting."""

    def test_consecutive_requests_wait_for_interval(self, tmp_path: Path) -> None:
        """Two consecutive requests enforce the configured minimum interval."""
        clock = {"now": 0.0}
        sleeps: list[float] = []
        transport = MockRestHttpTransport(default_response=_success_response())
        client, _ = build_test_rest_client(tmp_path, transport, is_vts=True)

        limiter = RateLimiter(
            min_interval_seconds=0.5,
            sleep_func=lambda seconds: sleeps.append(seconds),
            monotonic_func=lambda: clock["now"],
        )
        client._rate_limiter = limiter

        client.get("/uapi/test/v1/sample", "TEST0001")
        clock["now"] += 0.1
        client.get("/uapi/test/v1/sample", "TEST0001")

        assert sleeps == [pytest.approx(0.4)]
        assert transport.call_count == 2

    def test_vts_client_uses_official_vps_interval(self, tmp_path: Path) -> None:
        """VTS REST client uses 0.5s official interval."""
        transport = MockRestHttpTransport(default_response=_success_response())
        client, _ = build_test_rest_client(tmp_path, transport, is_vts=True)

        assert isinstance(client, KisRestClient)
        assert client._rate_limiter.min_interval_seconds == 0.5
