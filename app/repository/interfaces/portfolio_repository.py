"""Portfolio repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.portfolio.position import Position


class PortfolioRepository(Protocol):
    """Persistence contract for portfolio positions and snapshots."""

    def save_positions(self, account_no: str, positions: list[Position]) -> None:
        """Replace stored positions for an account."""

    def list_positions(self, account_no: str) -> list[Position]:
        """Return stored positions for an account."""

    def save_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        """Persist a portfolio snapshot and return its id."""

    def list_snapshots(self, account_no: str, *, limit: int = 50) -> list[PortfolioSnapshot]:
        """Return recent snapshots for an account."""

    def get_latest_snapshot(self, account_no: str) -> PortfolioSnapshot | None:
        """Return the latest snapshot for an account."""
