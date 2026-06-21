"""Unit tests for RetryPolicy."""

from __future__ import annotations

import pytest

from app.broker.kis.exceptions.rest_exceptions import BrokerTimeoutError, NetworkError
from app.broker.kis.rest.retry_policy import RetryPolicy
from app.config.config_models import RetryConfig

pytestmark = pytest.mark.unit


class TestRetryPolicy:
    """Tests for RetryPolicy."""

    def test_should_retry_network_error_for_get(self) -> None:
        """GET retries on network errors."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.should_retry(0, method="GET", error=NetworkError("down")) is True

    def test_should_retry_timeout_for_get(self) -> None:
        """GET retries on timeout errors."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.should_retry(0, method="GET", error=BrokerTimeoutError("slow")) is True

    def test_should_retry_http_503_for_get(self) -> None:
        """GET retries on retryable HTTP status codes."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.should_retry(0, method="GET", status_code=503) is True

    def test_should_not_retry_http_503_for_post(self) -> None:
        """POST does not retry server errors except rate limit."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.should_retry(0, method="POST", status_code=503) is False

    def test_should_retry_kis_rate_limit_code(self) -> None:
        """EGW00201 triggers retry."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.should_retry(0, method="POST", msg_cd="EGW00201") is True

    def test_should_not_retry_when_max_attempts_reached(self) -> None:
        """Retry stops after max_retry."""
        policy = RetryPolicy(RetryConfig(max_retry=2, backoff_factor=2))

        assert policy.should_retry(2, method="GET", status_code=503) is False

    def test_exponential_backoff_delay(self) -> None:
        """Backoff delay follows backoff_factor^attempt."""
        policy = RetryPolicy(RetryConfig(max_retry=3, backoff_factor=2))

        assert policy.delay_seconds(0) == 1.0
        assert policy.delay_seconds(1) == 2.0
        assert policy.delay_seconds(2) == 4.0
