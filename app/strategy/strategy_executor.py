"""Strategy method executor with error isolation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from app.domain.strategy.trading_signal import TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext


class StrategyExecutor:
    """Executes strategy callbacks and isolates failures."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def execute_market_data(
        self,
        strategy: BaseStrategy,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Run ``on_market_data`` safely."""
        return self._run(strategy.on_market_data, context, payload, method_name="on_market_data")

    def execute_execution(
        self,
        strategy: BaseStrategy,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Run ``on_execution`` safely."""
        return self._run(strategy.on_execution, context, payload, method_name="on_execution")

    def execute_portfolio_changed(
        self,
        strategy: BaseStrategy,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Run ``on_portfolio_changed`` safely."""
        return self._run(
            strategy.on_portfolio_changed,
            context,
            payload,
            method_name="on_portfolio_changed",
        )

    def _run(
        self,
        callback: Callable[[StrategyContext, dict[str, Any]], TradingSignal | None],
        context: StrategyContext,
        payload: dict[str, Any],
        *,
        method_name: str,
    ) -> TradingSignal | None:
        try:
            return callback(context, payload)
        except Exception:
            self._logger.exception(
                "Strategy execution failed id=%s method=%s",
                context.strategy_id,
                method_name,
            )
            return None
