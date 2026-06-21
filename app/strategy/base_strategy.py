"""Base strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.strategy.trading_signal import TradingSignal
from app.strategy.strategy_context import StrategyContext


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    strategy_type: str = "base"

    def __init__(
        self,
        *,
        strategy_id: str,
        name: str,
        symbols: tuple[str, ...],
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.strategy_id = strategy_id
        self.name = name
        self.symbols = symbols
        self.parameters = parameters or {}

    @abstractmethod
    def initialize(self, context: StrategyContext) -> None:
        """Prepare strategy state before execution."""

    @abstractmethod
    def on_start(self, context: StrategyContext) -> None:
        """Called when the strategy starts running."""

    @abstractmethod
    def on_market_data(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Handle incoming market data and optionally emit a signal."""

    def on_execution(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Handle execution notifications."""
        return None

    def on_portfolio_changed(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Handle portfolio update notifications."""
        return None

    @abstractmethod
    def on_stop(self, context: StrategyContext) -> None:
        """Called when the strategy stops."""
