"""Scheduled task type definitions."""

from __future__ import annotations

from enum import StrEnum


class ScheduledTaskType(StrEnum):
    """Supported scheduler task categories."""

    STRATEGY_AUTO_START = "strategy_auto_start"
    STRATEGY_AUTO_STOP = "strategy_auto_stop"
    BACKTEST_RUN = "backtest_run"
    PORTFOLIO_REFRESH = "portfolio_refresh"
    LOG_CLEANUP = "log_cleanup"
    PLUGIN_RESCAN = "plugin_rescan"
