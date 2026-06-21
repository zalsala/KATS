"""In-memory strategy repository."""

from __future__ import annotations

import threading

from app.domain.strategy.strategy import Strategy


class InMemoryStrategyRepository:
    """Thread-safe in-memory strategy storage."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._strategies: dict[str, Strategy] = {}

    def save(self, strategy: Strategy) -> None:
        """Persist a strategy."""
        with self._lock:
            self._strategies[strategy.strategy_id] = strategy

    def get(self, strategy_id: str) -> Strategy | None:
        """Load a strategy by ID."""
        with self._lock:
            return self._strategies.get(strategy_id)

    def list_all(self) -> list[Strategy]:
        """Return all stored strategies."""
        with self._lock:
            return list(self._strategies.values())

    def delete(self, strategy_id: str) -> bool:
        """Remove a strategy by ID."""
        with self._lock:
            return self._strategies.pop(strategy_id, None) is not None
