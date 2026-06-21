"""Scheduler application service."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.core.logging.logger_service import LoggerService
from app.events.event_bus_service import EventBusService
from app.plugins.plugin_manager import PluginManager
from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.scheduler_event_handler import SchedulerEventHandler
from app.scheduler.task_execution_result import TaskExecutionResult
from app.scheduler.task_executor import TaskExecutor
from app.scheduler.task_registry import TaskRegistry
from app.scheduler.task_scheduler import TaskScheduler
from app.service.backtest.backtest_service import BacktestService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.strategy.strategy_service import StrategyService


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class SchedulerService:
    """External entry point for scheduled task management and execution."""

    def __init__(
        self,
        *,
        registry: TaskRegistry | None = None,
        executor: TaskExecutor | None = None,
        scheduler: TaskScheduler | None = None,
        event_handler: SchedulerEventHandler | None = None,
        event_bus: EventBusService | None = None,
        strategy_service: StrategyService | None = None,
        backtest_service: BacktestService | None = None,
        portfolio_service: PortfolioService | None = None,
        plugin_manager: PluginManager | None = None,
        logger_service: LoggerService | None = None,
    ) -> None:
        self._registry = registry or TaskRegistry()
        self._event_bus = event_bus
        self._executor = executor or TaskExecutor(
            strategy_service=strategy_service,
            backtest_service=backtest_service,
            portfolio_service=portfolio_service,
            plugin_manager=plugin_manager,
            logger_service=logger_service,
        )
        self._scheduler = scheduler or TaskScheduler(
            registry=self._registry,
            executor=self._executor,
        )
        self._handler = event_handler or SchedulerEventHandler(event_bus=event_bus)
        self._logger = _resolve_logger()
        self._started = False

    @property
    def registry(self) -> TaskRegistry:
        return self._registry

    @property
    def scheduler(self) -> TaskScheduler:
        return self._scheduler

    @property
    def event_handler(self) -> SchedulerEventHandler:
        return self._handler

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Bind scheduler EventBus publishing."""
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start scheduler subscriptions"
            raise ValueError(msg)
        self._handler.register(bus)
        self._started = True
        self._logger.info("SchedulerService started")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unbind scheduler EventBus publishing."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

    def register_task(self, task: ScheduledTask) -> None:
        """Register a scheduled task."""
        with CorrelationContext():
            self._registry.register(task)
            self._logger.info(
                "Scheduled task registered id=%s type=%s",
                task.task_id,
                task.task_type,
            )

    def unregister_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        with CorrelationContext():
            removed = self._registry.unregister(task_id)
            if removed:
                self._logger.info("Scheduled task unregistered id=%s", task_id)
            return removed

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return registered task summaries."""
        return [
            {
                "task_id": task.task_id,
                "task_type": str(task.task_type),
                "enabled": task.enabled,
                "description": task.description,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            }
            for task in self._registry.list_all()
        ]

    def tick(self, *, now: datetime | None = None) -> list[TaskExecutionResult]:
        """Evaluate due tasks, execute them, and publish results."""
        with CorrelationContext():
            results = self._scheduler.tick(now=now)
            for result in results:
                self._handler.publish_task_result(result)
            return results

    def execute_task(self, task_id: str, *, now: datetime | None = None) -> TaskExecutionResult:
        """Execute one task immediately."""
        with CorrelationContext():
            result = self._scheduler.execute_task(task_id, now=now)
            self._handler.publish_task_result(result)
            return result


def build_scheduler_service(
    *,
    event_bus: EventBusService | None = None,
    strategy_service: StrategyService | None = None,
    backtest_service: BacktestService | None = None,
    portfolio_service: PortfolioService | None = None,
    plugin_manager: PluginManager | None = None,
    logger_service: LoggerService | None = None,
) -> SchedulerService:
    """Create a SchedulerService wired with default components."""
    return SchedulerService(
        event_bus=event_bus,
        strategy_service=strategy_service,
        backtest_service=backtest_service,
        portfolio_service=portfolio_service,
        plugin_manager=plugin_manager,
        logger_service=logger_service,
    )
