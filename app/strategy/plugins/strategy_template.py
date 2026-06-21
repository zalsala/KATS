"""Strategy template for custom implementations."""

from __future__ import annotations

from typing import Any

from app.domain.strategy.trading_signal import TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext


class StrategyTemplate(BaseStrategy):
    """No-op template strategy for extension."""

    strategy_type = "template"

    def initialize(self, context: StrategyContext) -> None:
        context.custom_state.setdefault("initialized", True)

    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["started"] = True

    def on_market_data(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        context.custom_state["stopped"] = True
