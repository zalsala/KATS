"""Retry policy for KIS REST API calls."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Final

from app.broker.kis.exceptions.rest_exceptions import BrokerTimeoutError, NetworkError
from app.config.config_models import RetryConfig

SleepFunc = Callable[[float], None]

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
KIS_RATE_LIMIT_MSG_CODE: Final[str] = "EGW00201"


class RetryPolicy:
    """Exponential backoff retry policy for REST requests."""

    def __init__(
        self,
        config: RetryConfig,
        *,
        sleep_func: SleepFunc | None = None,
    ) -> None:
        """Initialize retry policy.

        Args:
            config: Retry configuration from broker settings.
            sleep_func: Injectable sleep function for tests.
        """
        self._config = config
        self._sleep = sleep_func or time.sleep

    @property
    def max_retry(self) -> int:
        """Return maximum retry attempts."""
        return self._config.max_retry

    def should_retry(
        self,
        attempt: int,
        *,
        method: str,
        status_code: int | None = None,
        msg_cd: str | None = None,
        error: Exception | None = None,
    ) -> bool:
        """Determine whether another attempt should be made.

        Args:
            attempt: Zero-based attempt index for the failed call.
            method: HTTP method used for the request.
            status_code: HTTP status code when available.
            msg_cd: KIS message code when available.
            error: Raised transport exception when available.

        Returns:
            True when the request should be retried.
        """
        if attempt >= self._config.max_retry:
            return False

        if error is not None:
            return isinstance(error, (NetworkError, BrokerTimeoutError))

        if msg_cd == KIS_RATE_LIMIT_MSG_CODE:
            return True

        if method.upper() == "POST":
            return status_code == 429 or msg_cd == KIS_RATE_LIMIT_MSG_CODE

        return status_code in RETRYABLE_STATUS_CODES

    def delay_seconds(self, attempt: int) -> float:
        """Calculate backoff delay before the next retry.

        Args:
            attempt: Zero-based attempt index.

        Returns:
            Delay duration in seconds.
        """
        return float(self._config.backoff_factor**attempt)

    def wait_before_retry(self, attempt: int) -> float:
        """Sleep using exponential backoff.

        Args:
            attempt: Zero-based attempt index.

        Returns:
            Applied delay in seconds.
        """
        delay = self.delay_seconds(attempt)
        self._sleep(delay)
        return delay
