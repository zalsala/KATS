"""Strategy repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.strategy.strategy import Strategy


class StrategyRepository(Protocol):
    """Persistence contract for strategy metadata."""

    def save(self, strategy: Strategy) -> None:
        """Persist a strategy."""
        ...

    def get(self, strategy_id: str) -> Strategy | None:
        """Load a strategy by ID."""
        ...

    def list_all(self) -> list[Strategy]:
        """Return all stored strategies."""
        ...

    def delete(self, strategy_id: str) -> bool:
        """Remove a strategy by ID."""
        ...
