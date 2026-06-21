"""Backtest application service."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.backtest.backtest_runner import BacktestConfig, BacktestRunner, BacktestRunRequest
from app.backtest.historical_data_provider import HistoricalDataProvider
from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.domain.backtest.backtest_result import BacktestResult
from app.domain.risk.risk_policy import RiskPolicy


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class BacktestService:
    """External entry point for backtest execution."""

    def __init__(self, *, config: BacktestConfig | None = None) -> None:
        self._config = config or BacktestConfig()
        self._runner = BacktestRunner(config=self._config)
        self._logger = _resolve_logger()

    def run_backtest(
        self,
        *,
        provider: HistoricalDataProvider,
        strategy_type: str,
        strategy_name: str,
        symbols: list[str],
        parameters: dict[str, Any] | None = None,
        initial_capital: Decimal | None = None,
        risk_policy: RiskPolicy | None = None,
    ) -> BacktestResult:
        """Run a backtest and return performance metrics."""
        with CorrelationContext():
            capital = initial_capital or self._config.default_initial_capital
            request = BacktestRunRequest(
                provider=provider,
                strategy_type=strategy_type,
                strategy_name=strategy_name,
                symbols=symbols,
                parameters=parameters or {},
                initial_capital=capital,
                risk_policy=risk_policy,
            )
            result = self._runner.run(request)
            self._logger.info(
                "Backtest completed return_rate=%s trades=%s mdd=%s",
                result.total_return_rate,
                result.trade_count,
                result.max_drawdown,
            )
            return result


def build_backtest_service(*, config: BacktestConfig | None = None) -> BacktestService:
    """Create a BacktestService with default configuration."""
    return BacktestService(config=config)
