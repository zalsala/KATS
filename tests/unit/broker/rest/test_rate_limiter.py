"""Unit tests for RateLimiter."""

from __future__ import annotations

import pytest

from app.broker.kis.rest.rate_limiter import RateLimiter
from app.core.constants import KIS_RATE_LIMIT_SLEEP_PROD, KIS_RATE_LIMIT_SLEEP_VPS

pytestmark = pytest.mark.unit


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_from_vts_mode_uses_official_intervals(self) -> None:
        """VTS and prod modes use official smart_sleep values."""
        vts = RateLimiter.from_vts_mode(is_vts=True)
        prod = RateLimiter.from_vts_mode(is_vts=False)

        assert vts.min_interval_seconds == KIS_RATE_LIMIT_SLEEP_VPS
        assert prod.min_interval_seconds == KIS_RATE_LIMIT_SLEEP_PROD

    def test_acquire_waits_when_called_too_soon(self) -> None:
        """Second acquire waits for the minimum interval."""
        clock = {"now": 100.0}
        sleeps: list[float] = []

        def monotonic() -> float:
            return clock["now"]

        def sleep(seconds: float) -> None:
            sleeps.append(seconds)
            clock["now"] += seconds

        limiter = RateLimiter(
            min_interval_seconds=0.5,
            sleep_func=sleep,
            monotonic_func=monotonic,
        )
        limiter.acquire()
        clock["now"] += 0.1
        wait = limiter.acquire()

        assert wait == pytest.approx(0.4)
        assert sleeps == [pytest.approx(0.4)]
        assert limiter.wait_count == 1

    def test_acquire_no_wait_on_first_call(self) -> None:
        """First request does not wait."""
        sleeps: list[float] = []
        limiter = RateLimiter(min_interval_seconds=0.5, sleep_func=sleeps.append)

        wait = limiter.acquire()

        assert wait == 0.0
        assert sleeps == []
