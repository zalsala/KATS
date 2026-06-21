"""SQLite connection factory."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class SQLiteConnectionFactory:
    """Create SQLite connections for repository access."""

    def __init__(self, *, database_path: Path) -> None:
        self._database_path = database_path
        self._lock = threading.RLock()

    @property
    def database_path(self) -> Path:
        return self._database_path

    def connect(self) -> sqlite3.Connection:
        """Open a new SQLite connection with row access by column name."""
        with self._lock:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
