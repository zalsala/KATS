"""Background worker that periodically invokes SchedulerService.tick()."""

from __future__ import annotations

import logging
import threading

from app.service.scheduler.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerWorker:
    """Daemon thread that ticks the scheduler at a fixed interval."""

    def __init__(
        self,
        scheduler_service: SchedulerService,
        interval_seconds: float = 1.0,
    ) -> None:
        self._scheduler_service = scheduler_service
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Return True when the worker thread is alive."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the daemon worker thread if not already running."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="scheduler-worker",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "SchedulerWorker started (interval_seconds=%s)",
                self._interval_seconds,
            )

    def stop(self) -> None:
        """Signal the worker to stop and wait for the thread to exit."""
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                return
            self._stop_event.set()
            thread = self._thread

        thread.join(timeout=self._interval_seconds + 1.0)

        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None

        logger.info("SchedulerWorker stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._scheduler_service.tick()
            except Exception:
                logger.exception("Scheduler worker tick failed")
            self._stop_event.wait(self._interval_seconds)
