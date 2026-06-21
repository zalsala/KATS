"""SQLite system state repository helpers."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import utc_now_iso


class SQLiteSystemStateRepository(BaseRepository):
    """SQLite-backed key-value system state persistence."""

    def set_value(self, key: str, value: str) -> None:
        updated_at = utc_now_iso()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO system_state(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, updated_at),
            )

    def get_value(self, key: str) -> str | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM system_state WHERE key = ?",
                (key,),
            ).fetchone()
        return str(row["value"]) if row is not None else None

    def delete(self, key: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM system_state WHERE key = ?", (key,))
        return cursor.rowcount > 0
