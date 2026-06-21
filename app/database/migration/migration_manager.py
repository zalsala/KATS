"""Database migration manager."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.database.connection.sqlite_connection_factory import SQLiteConnectionFactory

logger = logging.getLogger(__name__)


class MigrationManager:
    """Apply SQL migration files in lexical order."""

    def __init__(
        self,
        *,
        connection_factory: SQLiteConnectionFactory,
        migrations_dir: Path | None = None,
    ) -> None:
        self._connection_factory = connection_factory
        if migrations_dir is None:
            migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
        self._migrations_dir = migrations_dir

    def migrate(self) -> list[str]:
        """Apply pending migrations and return applied versions."""
        applied: list[str] = []
        for migration_file in sorted(self._migrations_dir.glob("*.sql")):
            version = migration_file.stem
            if self._is_applied(version):
                continue
            sql = migration_file.read_text(encoding="utf-8")
            self._apply_migration(version=version, sql=sql)
            applied.append(version)
            logger.info("Applied migration %s", version)
        return applied

    def list_applied(self) -> list[str]:
        """Return applied migration versions."""
        try:
            with self._connection_factory.connect() as connection:
                rows = connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [str(row["version"]) for row in rows]

    def _is_applied(self, version: str) -> bool:
        try:
            with self._connection_factory.connect() as connection:
                row = connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = ?",
                    (version,),
                ).fetchone()
        except sqlite3.OperationalError:
            return False
        return row is not None

    def _apply_migration(self, *, version: str, sql: str) -> None:
        with self._connection_factory.connect() as connection:
            connection.executescript(sql)
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, datetime.now(UTC).isoformat()),
            )
            connection.commit()
