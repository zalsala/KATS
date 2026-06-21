"""Scheduler EventBus integration."""

from __future__ import annotations

from app.events.domain_events import SystemEvent
from app.events.event_bus_service import EventBusService
from app.scheduler.task_execution_result import TaskExecutionResult


class SchedulerEventHandler:
    """Publish scheduler execution results to EventBus."""

    def __init__(self, *, event_bus: EventBusService | None = None) -> None:
        self._event_bus = event_bus
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Scheduler currently publishes only; no inbound subscriptions."""
        self._event_bus = event_bus
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Clear scheduler EventBus bindings."""
        _ = event_bus
        self._subscription_ids.clear()

    def publish_task_result(self, result: TaskExecutionResult) -> None:
        """Publish a task execution result as a SystemEvent."""
        if self._event_bus is None:
            return
        event_name = (
            "scheduler.task.skipped"
            if result.skipped
            else ("scheduler.task.completed" if result.success else "scheduler.task.failed")
        )
        self._event_bus.publish(
            SystemEvent(
                source="scheduler",
                event_name=event_name,
                payload={
                    "task_id": result.task_id,
                    "task_type": str(result.task_type),
                    "success": result.success,
                    "skipped": result.skipped,
                    "message": result.message,
                    "result_payload": result.payload,
                    "executed_at": result.executed_at.isoformat(),
                },
            )
        )
