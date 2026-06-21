"""Strategy lifecycle manager."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_state import StrategyState
from app.domain.strategy.trading_signal import TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext
from app.strategy.strategy_registry import StrategyRegistry


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


@dataclass(slots=True)
class ManagedStrategy:
    """Runtime bundle of strategy metadata and instance."""

    entity: Strategy
    instance: BaseStrategy
    context: StrategyContext


class StrategyManager:
    """Registers, starts, stops, and tracks multiple strategies."""

    def __init__(self, *, registry: StrategyRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()
        self._managed: dict[str, ManagedStrategy] = {}
        self._logger = _resolve_logger()

    def register(self, entity: Strategy) -> ManagedStrategy:
        """Create a runtime strategy instance from metadata."""
        instance = self._registry.create(
            entity.strategy_type,
            strategy_id=entity.strategy_id,
            name=entity.name,
            symbols=entity.symbols,
            parameters=entity.parameters,
        )
        context = StrategyContext(
            strategy_id=entity.strategy_id,
            strategy_name=entity.name,
            symbols=entity.symbols,
            parameters=dict(entity.parameters),
            logger=self._logger,
        )
        managed = ManagedStrategy(entity=entity, instance=instance, context=context)
        with self._lock:
            self._managed[entity.strategy_id] = managed
        return managed

    def get(self, strategy_id: str) -> ManagedStrategy | None:
        """Return a managed strategy by ID."""
        with self._lock:
            return self._managed.get(strategy_id)

    def list_managed(self) -> list[ManagedStrategy]:
        """Return all managed strategies."""
        with self._lock:
            return list(self._managed.values())

    def get_running_for_symbol(self, symbol_code: str) -> list[ManagedStrategy]:
        """Return running strategies subscribed to a symbol."""
        with self._lock:
            return [
                managed
                for managed in self._managed.values()
                if managed.entity.state == StrategyState.RUNNING
                and managed.entity.enabled
                and symbol_code in managed.entity.symbols
            ]

    def start(self, strategy_id: str) -> None:
        """Initialize and start a strategy."""
        managed = self._require(strategy_id)
        if managed.entity.state == StrategyState.RUNNING:
            return
        managed.instance.initialize(managed.context)
        managed.entity.state = StrategyState.INITIALIZED
        managed.instance.on_start(managed.context)
        managed.entity.state = StrategyState.RUNNING
        self._logger.info("Strategy started id=%s name=%s", strategy_id, managed.entity.name)

    def stop(self, strategy_id: str) -> None:
        """Stop a running strategy."""
        managed = self._require(strategy_id)
        if managed.entity.state in {StrategyState.STOPPED, StrategyState.DISPOSED}:
            return
        managed.instance.on_stop(managed.context)
        managed.entity.state = StrategyState.STOPPED
        self._logger.info("Strategy stopped id=%s name=%s", strategy_id, managed.entity.name)

    def pause(self, strategy_id: str) -> None:
        """Pause a running strategy."""
        managed = self._require(strategy_id)
        if managed.entity.state == StrategyState.RUNNING:
            managed.entity.state = StrategyState.PAUSED

    def resume(self, strategy_id: str) -> None:
        """Resume a paused strategy."""
        managed = self._require(strategy_id)
        if managed.entity.state == StrategyState.PAUSED:
            managed.entity.state = StrategyState.RUNNING

    def update_portfolio_snapshot(self, strategy_id: str, snapshot: Any) -> None:
        """Update portfolio snapshot on a strategy context."""
        managed = self._require(strategy_id)
        managed.context.portfolio_snapshot = snapshot

    def update_price(self, symbol_code: str, price: Any) -> None:
        """Update cached price for all managed strategies."""
        with self._lock:
            for managed in self._managed.values():
                managed.context.price_cache[symbol_code] = price

    def record_signal(self, strategy_id: str, signal: TradingSignal) -> None:
        """Update strategy statistics after signal generation."""
        managed = self._require(strategy_id)
        stats = managed.entity.statistics
        if stats is None:
            return
        stats.record_signal(signal.signal_type.value, at=signal.timestamp)

    def record_market_data(self, strategy_id: str) -> None:
        """Increment market data counter."""
        managed = self._require(strategy_id)
        stats = managed.entity.statistics
        if stats is not None:
            stats.market_data_count += 1

    def record_execution(self, strategy_id: str) -> None:
        """Increment execution counter."""
        managed = self._require(strategy_id)
        stats = managed.entity.statistics
        if stats is not None:
            stats.execution_count += 1

    def _require(self, strategy_id: str) -> ManagedStrategy:
        managed = self.get(strategy_id)
        if managed is None:
            msg = f"Strategy not found: {strategy_id}"
            raise KeyError(msg)
        return managed
