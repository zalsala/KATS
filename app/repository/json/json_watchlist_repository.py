"""JSON-backed watchlist persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.repository.interfaces.watchlist_repository import (
    WatchlistSnapshot,
    WatchlistSnapshotItem,
)

logger = logging.getLogger(__name__)

DEFAULT_WATCHLIST_FILE = "watchlist.json"


class JsonWatchlistRepository:
    """Persist watchlist state to ``data/watchlist.json``."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def from_project_root(cls, project_root: Path) -> JsonWatchlistRepository:
        """Create a repository using the standard data directory."""
        return cls(project_root / "data" / DEFAULT_WATCHLIST_FILE)

    def load(self) -> WatchlistSnapshot:
        """Load watchlist state from disk."""
        if not self._path.exists():
            return WatchlistSnapshot(selected_symbol=None, items=())

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load watchlist from %s", self._path)
            return WatchlistSnapshot(selected_symbol=None, items=())

        selected_symbol = raw.get("selected_symbol")
        if selected_symbol is not None:
            selected_symbol = str(selected_symbol).strip() or None

        items: list[WatchlistSnapshotItem] = []
        for entry in raw.get("items", []):
            symbol_code = str(entry.get("symbol_code", "")).strip()
            if not symbol_code:
                continue
            name = str(entry.get("name", symbol_code)).strip() or symbol_code
            items.append(WatchlistSnapshotItem(symbol_code=symbol_code, name=name))

        return WatchlistSnapshot(selected_symbol=selected_symbol, items=tuple(items))

    def save(self, snapshot: WatchlistSnapshot) -> None:
        """Persist watchlist state to disk."""
        payload = {
            "selected_symbol": snapshot.selected_symbol,
            "items": [
                {"symbol_code": item.symbol_code, "name": item.name} for item in snapshot.items
            ],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
