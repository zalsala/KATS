"""Watchlist persistence contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WatchlistSnapshotItem:
    """Persisted watchlist row without live quote fields."""

    symbol_code: str
    name: str


@dataclass(frozen=True, slots=True)
class WatchlistSnapshot:
    """Persisted watchlist state."""

    selected_symbol: str | None
    items: tuple[WatchlistSnapshotItem, ...]


class WatchlistRepository(Protocol):
    """Persistence contract for watchlist state."""

    def load(self) -> WatchlistSnapshot:
        """Load watchlist state from storage."""

    def save(self, snapshot: WatchlistSnapshot) -> None:
        """Persist watchlist state."""
