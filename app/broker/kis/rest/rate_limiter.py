"""Rate limiter for KIS REST API calls."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from app.core.constants import KIS_RATE_LIMIT_SLEEP_PROD, KIS_RATE_LIMIT_SLEEP_VPS

SleepFunc = Callable[[float], None]
MonotonicFunc = Callable[[], float]


class RateLimiter:
    """Thread-safe minimum-interval rate limiter."""

    def __init__(
        self,
        *,
        min_interval_seconds: float,
        sleep_func: SleepFunc | None = None,
        monotonic_func: MonotonicFunc | None = None,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            min_interval_seconds: Minimum delay between consecutive requests.
            sleep_func: Injectable sleep function for tests.
            monotonic_func: Injectable monotonic clock for tests.
        """
        self._min_interval_seconds = min_interval_seconds
        self._sleep = sleep_func or time.sleep
        self._monotonic = monotonic_func or time.monotonic
        self._lock = threading.Lock()
        self._last_request_at: float | None = None
        self.wait_count: int = 0

    @classmethod
    def from_vts_mode(cls, *, is_vts: bool) -> RateLimiter:
        """Create a limiter using official KIS smart_sleep values.

        Args:
            is_vts: True for mock/VTS environment.

        Returns:
            Configured ``RateLimiter`` instance.
        """
        interval = KIS_RATE_LIMIT_SLEEP_VPS if is_vts else KIS_RATE_LIMIT_SLEEP_PROD
        return cls(min_interval_seconds=interval)

    @property
    def min_interval_seconds(self) -> float:
        """Return configured minimum interval."""
        return self._min_interval_seconds

    def acquire(self) -> float:
        """Wait until the next request is allowed.

        Returns:
            Actual wait duration in seconds.
        """
        with self._lock:
            now = self._monotonic()
            wait_seconds = 0.0
            if self._last_request_at is not None:
                elapsed = now - self._last_request_at
                if elapsed < self._min_interval_seconds:
                    wait_seconds = self._min_interval_seconds - elapsed
                    self._sleep(wait_seconds)
                    self.wait_count += 1
            self._last_request_at = self._monotonic()
            return wait_seconds
