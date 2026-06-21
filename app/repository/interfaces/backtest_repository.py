"""Backtest repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.backtest.backtest_result import BacktestResult


class BacktestRepository(Protocol):
    """Persistence contract for backtest results."""

    def save(
        self,
        result: BacktestResult,
        *,
        strategy_type: str,
        strategy_name: str,
        symbols: list[str],
    ) -> int:
        """Persist a backtest result and return its id."""

    def get(self, result_id: int) -> BacktestResult | None:
        """Load a backtest result by id."""

    def list_all(self, *, limit: int = 50) -> list[tuple[int, BacktestResult]]:
        """Return stored backtest results."""
