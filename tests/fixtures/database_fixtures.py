"""Shared database test fixtures."""

from __future__ import annotations

from pathlib import Path

from app.database.database_manager import DatabaseManager


def build_test_database_manager(tmp_path: Path) -> DatabaseManager:
    """Build an initialized DatabaseManager using a temporary SQLite file."""
    database_path = tmp_path / "test.db"
    manager = DatabaseManager(database_path=database_path, migration_enabled=True)
    manager.initialize()
    return manager
