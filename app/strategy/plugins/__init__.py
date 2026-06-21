"""Strategy plugin exports."""

from app.strategy.plugins.buy_and_hold_strategy import BuyAndHoldStrategy
from app.strategy.plugins.moving_average_cross_strategy import MovingAverageCrossStrategy
from app.strategy.plugins.rsi_strategy import RSIStrategy
from app.strategy.plugins.strategy_template import StrategyTemplate

__all__ = [
    "BuyAndHoldStrategy",
    "MovingAverageCrossStrategy",
    "RSIStrategy",
    "StrategyTemplate",
]
