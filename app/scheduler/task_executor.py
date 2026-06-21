"""Scheduled task execution via application services."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.core.logging.logger_service import LoggerService
from app.plugins.plugin_manager import PluginManager
from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.task_execution_result import TaskExecutionResult
from app.scheduler.task_types import ScheduledTaskType
from app.service.backtest.backtest_service import BacktestService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.strategy.strategy_service import StrategyService


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


class TaskExecutor:
    """Execute scheduled tasks through application services only."""

    def __init__(
        self,
        *,
        strategy_service: StrategyService | None = None,
        backtest_service: BacktestService | None = None,
        portfolio_service: PortfolioService | None = None,
        plugin_manager: PluginManager | None = None,
        logger_service: LoggerService | None = None,
    ) -> None:
        self._strategy_service = strategy_service
        self._backtest_service = backtest_service
        self._portfolio_service = portfolio_service
        self._plugin_manager = plugin_manager
        self._logger_service = logger_service
        self._logger = _resolve_logger()

    def execute(self, task: ScheduledTask) -> TaskExecutionResult:
        """Run a scheduled task and return the execution result."""
        handlers = {
            ScheduledTaskType.STRATEGY_AUTO_START: self._execute_strategy_start,
            ScheduledTaskType.STRATEGY_AUTO_STOP: self._execute_strategy_stop,
            ScheduledTaskType.BACKTEST_RUN: self._execute_backtest,
            ScheduledTaskType.PORTFOLIO_REFRESH: self._execute_portfolio_refresh,
            ScheduledTaskType.LOG_CLEANUP: self._execute_log_cleanup,
            ScheduledTaskType.PLUGIN_RESCAN: self._execute_plugin_rescan,
        }
        handler = handlers.get(task.task_type)
        if handler is None:
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                message=f"Unsupported task type: {task.task_type}",
            )
        try:
            return handler(task)
        except Exception as exc:  # noqa: BLE001 - task failures must not stop scheduler
            self._logger.exception(
                "Scheduled task failed id=%s type=%s", task.task_id, task.task_type
            )
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                message=str(exc),
            )

    def _execute_strategy_start(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._strategy_service is None:
            return self._missing_service(task, "StrategyService")
        strategy_id = str(task.payload.get("strategy_id", ""))
        if not strategy_id:
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                message="strategy_id is required",
            )
        dto = self._strategy_service.start_strategy(strategy_id)
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={"strategy_id": dto.strategy_id, "state": dto.state},
            message="strategy started",
        )

    def _execute_strategy_stop(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._strategy_service is None:
            return self._missing_service(task, "StrategyService")
        strategy_id = str(task.payload.get("strategy_id", ""))
        if not strategy_id:
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                message="strategy_id is required",
            )
        dto = self._strategy_service.stop_strategy(strategy_id)
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={"strategy_id": dto.strategy_id, "state": dto.state},
            message="strategy stopped",
        )

    def _execute_backtest(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._backtest_service is None:
            return self._missing_service(task, "BacktestService")
        provider = task.payload.get("provider")
        if provider is None:
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                message="provider is required",
            )
        result = self._backtest_service.run_backtest(
            provider=provider,
            strategy_type=str(task.payload.get("strategy_type", "template")),
            strategy_name=str(task.payload.get("strategy_name", "scheduled-backtest")),
            symbols=list(task.payload.get("symbols", [])),
            parameters=dict(task.payload.get("parameters", {})),
            initial_capital=_to_decimal(task.payload.get("initial_capital")),
        )
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={
                "total_return_rate": str(result.total_return_rate),
                "trade_count": result.trade_count,
                "max_drawdown": str(result.max_drawdown),
            },
            message="backtest completed",
        )

    def _execute_portfolio_refresh(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._portfolio_service is None:
            return self._missing_service(task, "PortfolioService")
        snapshot = self._portfolio_service.get_snapshot()
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={
                "account_no": snapshot.account_no,
                "total_asset": str(snapshot.total_asset),
                "position_count": len(snapshot.positions),
            },
            message="portfolio refreshed",
        )

    def _execute_log_cleanup(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._logger_service is None:
            return self._missing_service(task, "LoggerService")
        max_age_days = int(task.payload.get("max_age_days", 7))
        deleted_count = self._logger_service.cleanup_old_logs(max_age_days=max_age_days)
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={"deleted_count": deleted_count, "max_age_days": max_age_days},
            message="log cleanup completed",
        )

    def _execute_plugin_rescan(self, task: ScheduledTask) -> TaskExecutionResult:
        if self._plugin_manager is None:
            return self._missing_service(task, "PluginManager")
        report = self._plugin_manager.load_all()
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=True,
            payload={
                "loaded": list(report.loaded),
                "skipped": list(report.skipped),
                "error_count": len(report.errors),
            },
            message="plugin rescan completed",
        )

    def _missing_service(self, task: ScheduledTask, service_name: str) -> TaskExecutionResult:
        return TaskExecutionResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=False,
            message=f"{service_name} is not configured",
        )


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
