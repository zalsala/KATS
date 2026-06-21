"""Task execution tests."""

from __future__ import annotations

import pytest
from tests.fixtures.backtest_fixtures import build_sample_provider
from tests.fixtures.scheduler_fixtures import (
    build_mock_plugin_manager,
    build_test_scheduler_service,
    utc_at,
)

from app.config.config_models import LoggingConfig
from app.core.logging.logger_service import LoggerService
from app.scheduler.rules import IntervalRule
from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.task_types import ScheduledTaskType
from app.service.backtest.backtest_service import BacktestService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.strategy.strategy_service import StrategyService

pytestmark = pytest.mark.unit


def test_execute_strategy_auto_start() -> None:
    strategy_service = StrategyService()
    dto = strategy_service.register_strategy(
        strategy_type="template",
        name="scheduled-template",
        symbols=["005930"],
    )
    scheduler = build_test_scheduler_service(strategy_service=strategy_service)
    scheduler.register_task(
        ScheduledTask(
            task_id="start-template",
            task_type=ScheduledTaskType.STRATEGY_AUTO_START,
            rule=IntervalRule(interval_seconds=1),
            payload={"strategy_id": dto.strategy_id},
        )
    )
    result = scheduler.execute_task("start-template", now=utc_at(2024, 1, 1, 0, 0))
    assert result.success is True
    assert result.payload["state"] == "running"


def test_execute_backtest_task() -> None:
    scheduler = build_test_scheduler_service(backtest_service=BacktestService())
    scheduler.register_task(
        ScheduledTask(
            task_id="backtest-1",
            task_type=ScheduledTaskType.BACKTEST_RUN,
            rule=IntervalRule(interval_seconds=1),
            payload={
                "provider": build_sample_provider(),
                "strategy_type": "template",
                "strategy_name": "scheduled-backtest",
                "symbols": ["005930"],
            },
        )
    )
    result = scheduler.execute_task("backtest-1", now=utc_at(2024, 1, 1, 0, 0))
    assert result.success is True
    assert result.payload["trade_count"] >= 0


def test_execute_portfolio_refresh_task() -> None:
    scheduler = build_test_scheduler_service(
        portfolio_service=PortfolioService(account_no="sched-account")
    )
    scheduler.register_task(
        ScheduledTask(
            task_id="portfolio-refresh",
            task_type=ScheduledTaskType.PORTFOLIO_REFRESH,
            rule=IntervalRule(interval_seconds=1),
        )
    )
    result = scheduler.execute_task("portfolio-refresh", now=utc_at(2024, 1, 1, 0, 0))
    assert result.success is True
    assert result.payload["account_no"] == "sched-account"


def test_execute_plugin_rescan_task() -> None:
    plugin_manager = build_mock_plugin_manager()
    scheduler = build_test_scheduler_service(plugin_manager=plugin_manager)
    scheduler.register_task(
        ScheduledTask(
            task_id="plugin-rescan",
            task_type=ScheduledTaskType.PLUGIN_RESCAN,
            rule=IntervalRule(interval_seconds=1),
        )
    )
    result = scheduler.execute_task("plugin-rescan", now=utc_at(2024, 1, 1, 0, 0))
    assert result.success is True
    plugin_manager.load_all.assert_called_once()


def test_execute_log_cleanup_task(tmp_path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    old_log = logs_dir / "old.log"
    old_log.write_text("old", encoding="utf-8")

    logger_service = LoggerService.get_instance()
    logger_service.setup(LoggingConfig(), logs_dir)

    scheduler = build_test_scheduler_service(logger_service=logger_service)
    scheduler.register_task(
        ScheduledTask(
            task_id="log-cleanup",
            task_type=ScheduledTaskType.LOG_CLEANUP,
            rule=IntervalRule(interval_seconds=1),
            payload={"max_age_days": 0},
        )
    )
    result = scheduler.execute_task("log-cleanup", now=utc_at(2024, 1, 1, 0, 0))
    assert result.success is True
    assert result.payload["deleted_count"] >= 0
