"""Shared scheduler test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.core.logging.logger_service import LoggerService
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.plugins.plugin_manager import PluginLoadReport, PluginManager
from app.scheduler.rules import IntervalRule
from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.task_types import ScheduledTaskType
from app.service.backtest.backtest_service import BacktestService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.scheduler.scheduler_service import SchedulerService
from app.service.strategy.strategy_service import StrategyService


def build_test_event_bus_service() -> EventBusService:
    """Build EventBusService with a fresh in-memory bus."""
    return EventBusService(event_bus=InMemoryEventBus())


def build_test_scheduler_service(
    *,
    strategy_service: StrategyService | None = None,
    backtest_service: BacktestService | None = None,
    portfolio_service: PortfolioService | None = None,
    plugin_manager: PluginManager | None = None,
    logger_service: LoggerService | None = None,
) -> SchedulerService:
    """Build SchedulerService with optional dependencies."""
    return SchedulerService(
        event_bus=build_test_event_bus_service(),
        strategy_service=strategy_service,
        backtest_service=backtest_service,
        portfolio_service=portfolio_service,
        plugin_manager=plugin_manager,
        logger_service=logger_service,
    )


def build_interval_task(
    *,
    task_id: str = "task-1",
    task_type: ScheduledTaskType = ScheduledTaskType.PORTFOLIO_REFRESH,
    interval_seconds: int = 60,
    payload: dict | None = None,
) -> ScheduledTask:
    """Build a simple interval scheduled task."""
    return ScheduledTask(
        task_id=task_id,
        task_type=task_type,
        rule=IntervalRule(interval_seconds=interval_seconds),
        payload=payload or {},
    )


def utc_at(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """Build a UTC datetime helper."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


class MockPluginManager:
    """Minimal plugin manager stub for scheduler tests."""

    def __init__(self) -> None:
        self.load_count = 0

    def load_all(self) -> PluginLoadReport:
        self.load_count += 1
        return PluginLoadReport(loaded=["example"], skipped=[], errors=[])


def build_mock_plugin_manager() -> MagicMock:
    """Return a MagicMock configured like PluginManager."""
    manager = MagicMock(spec=PluginManager)
    manager.load_all.return_value = PluginLoadReport(loaded=["example"], skipped=[], errors=[])
    return manager
