"""WebSocket reconnect manager."""

from __future__ import annotations

import time
from collections.abc import Callable

SleepFunc = Callable[[float], None]


class ReconnectManager:
    """Manages reconnect attempts with exponential backoff."""

    def __init__(
        self,
        *,
        max_attempts: int = 5,
        base_delay_seconds: float = 1.0,
        sleep_func: SleepFunc | None = None,
    ) -> None:
        self._max_attempts = max_attempts
        self._base_delay_seconds = base_delay_seconds
        self._sleep = sleep_func or time.sleep
        self._attempts = 0

    @property
    def attempts(self) -> int:
        """Return current reconnect attempt count."""
        return self._attempts

    def should_retry(self) -> bool:
        """Return True when another reconnect attempt is allowed."""
        return self._attempts < self._max_attempts

    def record_attempt(self) -> None:
        """Increment reconnect attempt counter."""
        self._attempts += 1

    def reset(self) -> None:
        """Reset reconnect attempt counter after a successful connection."""
        self._attempts = 0

    def wait_before_retry(self) -> float:
        """Sleep using exponential backoff and return applied delay."""
        delay = float(self._base_delay_seconds * (2**self._attempts))
        self._sleep(delay)
        return delay
