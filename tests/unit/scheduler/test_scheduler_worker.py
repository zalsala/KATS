"""Unit tests for SchedulerWorker."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from app.scheduler.scheduler_worker import SchedulerWorker

pytestmark = pytest.mark.unit


def test_worker_start_sets_running() -> None:
    scheduler = MagicMock()
    worker = SchedulerWorker(scheduler, interval_seconds=1.0)

    worker.start()

    try:
        assert worker.is_running is True
    finally:
        worker.stop()


def test_worker_stop_clears_running() -> None:
    scheduler = MagicMock()
    worker = SchedulerWorker(scheduler, interval_seconds=1.0)
    worker.start()
    worker.stop()

    assert worker.is_running is False


def test_worker_invokes_tick_periodically() -> None:
    scheduler = MagicMock()
    worker = SchedulerWorker(scheduler, interval_seconds=0.05)
    worker.start()

    try:
        time.sleep(0.15)
        assert scheduler.tick.call_count > 0
    finally:
        worker.stop()


def test_worker_continues_after_tick_exception() -> None:
    scheduler = MagicMock()
    scheduler.tick.side_effect = [RuntimeError("boom"), None, None]
    worker = SchedulerWorker(scheduler, interval_seconds=0.05)
    worker.start()

    try:
        time.sleep(0.15)
        assert scheduler.tick.call_count >= 2
        assert worker.is_running is True
    finally:
        worker.stop()


def test_worker_duplicate_start_is_idempotent() -> None:
    scheduler = MagicMock()
    worker = SchedulerWorker(scheduler, interval_seconds=0.05)
    worker.start()
    first_thread = worker._thread  # noqa: SLF001

    worker.start()

    try:
        assert worker.is_running is True
        assert worker._thread is first_thread  # noqa: SLF001
    finally:
        worker.stop()
