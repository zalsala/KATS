"""Strategy plugin with forbidden import."""

from __future__ import annotations

from app.service.order.order_service import OrderService
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext


class ForbiddenStrategy(BaseStrategy):
    """Invalid plugin that imports OrderService."""

    strategy_type = "forbidden_strategy"

    def initialize(self, context: StrategyContext) -> None:
        _ = OrderService

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_market_data(self, context: StrategyContext, payload: dict) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None
