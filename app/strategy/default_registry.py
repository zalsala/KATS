"""Default strategy plugin registration."""

from __future__ import annotations

from app.strategy.plugins.buy_and_hold_strategy import BuyAndHoldStrategy
from app.strategy.plugins.moving_average_cross_strategy import MovingAverageCrossStrategy
from app.strategy.plugins.rsi_strategy import RSIStrategy
from app.strategy.plugins.strategy_template import StrategyTemplate
from app.strategy.strategy_registry import StrategyRegistry


def register_default_strategies(registry: StrategyRegistry) -> None:
    """Register built-in strategy plugins."""
    registry.register(BuyAndHoldStrategy.strategy_type, BuyAndHoldStrategy)
    registry.register(MovingAverageCrossStrategy.strategy_type, MovingAverageCrossStrategy)
    registry.register(RSIStrategy.strategy_type, RSIStrategy)
    registry.register(StrategyTemplate.strategy_type, StrategyTemplate)
