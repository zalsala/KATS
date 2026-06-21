"""ReconnectManager tests."""

from __future__ import annotations

import pytest

from app.broker.kis.websocket.reconnect_manager import ReconnectManager

pytestmark = pytest.mark.unit


class TestReconnectManager:
    """Tests for WebSocket ReconnectManager."""

    def test_exponential_backoff(self) -> None:
        sleeps: list[float] = []
        manager = ReconnectManager(
            max_attempts=3,
            base_delay_seconds=1.0,
            sleep_func=sleeps.append,
        )

        assert manager.should_retry() is True
        manager.record_attempt()
        delay = manager.wait_before_retry()

        assert delay == 2.0
        assert sleeps == [2.0]

    def test_reset_clears_attempts(self) -> None:
        manager = ReconnectManager(
            max_attempts=2, base_delay_seconds=0.1, sleep_func=lambda _: None
        )
        manager.record_attempt()
        manager.reset()

        assert manager.attempts == 0

    def test_stops_after_max_attempts(self) -> None:
        manager = ReconnectManager(
            max_attempts=2, base_delay_seconds=0.1, sleep_func=lambda _: None
        )
        manager.record_attempt()
        manager.record_attempt()

        assert manager.should_retry() is False
