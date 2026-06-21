"""Indicator registry for plugin-backed indicators."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from app.plugins.base_indicator import BaseIndicator

IndicatorFactory = Callable[..., BaseIndicator]


class IndicatorRegistry:
    """Maps indicator names to plugin indicator factories."""

    def __init__(self) -> None:
        self._factories: dict[str, IndicatorFactory] = {}

    def register(self, indicator_name: str, factory: IndicatorFactory) -> None:
        """Register an indicator factory by name."""
        self._factories[indicator_name] = factory

    def create(self, indicator_name: str, **parameters: Any) -> BaseIndicator:
        """Instantiate an indicator from a registered name."""
        factory = self._factories.get(indicator_name)
        if factory is None:
            msg = f"Unknown indicator: {indicator_name}"
            raise ValueError(msg)
        return factory(**parameters)

    def compute(
        self,
        indicator_name: str,
        prices: list[Decimal],
        **parameters: Any,
    ) -> Decimal | None:
        """Compute an indicator value using a registered plugin."""
        indicator = self.create(indicator_name, **parameters)
        return indicator.compute(prices, **parameters)

    def list_names(self) -> tuple[str, ...]:
        """Return registered indicator names."""
        return tuple(sorted(self._factories))

    def is_registered(self, indicator_name: str) -> bool:
        """Return whether an indicator name is registered."""
        return indicator_name in self._factories
