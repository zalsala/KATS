"""In-memory portfolio store."""

from __future__ import annotations

import threading
from collections.abc import Callable

from app.domain.portfolio.portfolio import Portfolio
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot


class InMemoryPortfolioStore:
    """Thread-safe in-memory portfolio storage."""

    def __init__(self, *, account_no: str = "") -> None:
        self._lock = threading.RLock()
        self._portfolio = Portfolio(account_no=account_no)

    def get(self) -> Portfolio:
        """Return the current portfolio."""
        with self._lock:
            return self._portfolio

    def save(self, portfolio: Portfolio) -> None:
        """Replace the current portfolio."""
        with self._lock:
            self._portfolio = portfolio

    def snapshot(self) -> PortfolioSnapshot:
        """Return an immutable snapshot of the current portfolio."""
        with self._lock:
            return PortfolioSnapshot.from_portfolio(self._portfolio)

    def load_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Replace the current portfolio from a persisted snapshot."""
        with self._lock:
            self._portfolio = Portfolio(
                account_no=snapshot.account_no,
                cash=snapshot.cash,
                positions={position.symbol_code: position for position in snapshot.positions},
                updated_at=snapshot.updated_at,
            )

    def update(self, updater: Callable[[Portfolio], None]) -> PortfolioSnapshot:
        """Apply an updater function and persist the result."""
        with self._lock:
            updater(self._portfolio)
            self._portfolio.touch()
            return PortfolioSnapshot.from_portfolio(self._portfolio)
