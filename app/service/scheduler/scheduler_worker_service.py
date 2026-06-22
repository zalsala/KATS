"""Application service wrapper for the scheduler background worker."""

from __future__ import annotations

from app.scheduler.scheduler_worker import SchedulerWorker
from app.service.scheduler.scheduler_service import SchedulerService


class SchedulerWorkerService:
    """Manage the lifecycle of a SchedulerWorker."""

    def __init__(self, worker: SchedulerWorker) -> None:
        self._worker = worker

    @property
    def is_running(self) -> bool:
        """Return True when the background worker thread is active."""
        return self._worker.is_running

    def start(self) -> None:
        """Start the background scheduler worker."""
        self._worker.start()

    def stop(self) -> None:
        """Stop the background scheduler worker."""
        self._worker.stop()


def build_scheduler_worker_service(
    scheduler_service: SchedulerService,
    *,
    interval_seconds: float = 1.0,
) -> SchedulerWorkerService:
    """Create a SchedulerWorkerService wired to the given scheduler."""
    return SchedulerWorkerService(
        SchedulerWorker(scheduler_service, interval_seconds=interval_seconds),
    )
