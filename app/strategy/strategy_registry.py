"""Strategy type registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.strategy.base_strategy import BaseStrategy

StrategyFactory = Callable[..., BaseStrategy]


class StrategyRegistry:
    """Maps strategy type names to factory callables."""

    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, strategy_type: str, factory: StrategyFactory) -> None:
        """Register a strategy factory by type name."""
        self._factories[strategy_type] = factory

    def create(
        self,
        strategy_type: str,
        *,
        strategy_id: str,
        name: str,
        symbols: tuple[str, ...],
        parameters: dict[str, Any] | None = None,
    ) -> BaseStrategy:
        """Instantiate a strategy from a registered type."""
        factory = self._factories.get(strategy_type)
        if factory is None:
            msg = f"Unknown strategy type: {strategy_type}"
            raise ValueError(msg)
        return factory(
            strategy_id=strategy_id,
            name=name,
            symbols=symbols,
            parameters=parameters,
        )

    def list_types(self) -> tuple[str, ...]:
        """Return registered strategy type names."""
        return tuple(sorted(self._factories))

    def is_registered(self, strategy_type: str) -> bool:
        """Return whether a strategy type is registered."""
        return strategy_type in self._factories
