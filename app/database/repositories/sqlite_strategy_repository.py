"""SQLite strategy repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import row_to_strategy, strategy_to_row, utc_now_iso
from app.domain.strategy.strategy import Strategy


class SQLiteStrategyRepository(BaseRepository):
    """SQLite-backed strategy persistence."""

    def save(self, strategy: Strategy) -> None:
        existing = self.get(strategy.strategy_id)
        timestamps = {
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        if existing is not None:
            with self._connection() as connection:
                row = connection.execute(
                    "SELECT created_at FROM strategies WHERE strategy_id = ?",
                    (strategy.strategy_id,),
                ).fetchone()
            if row is not None:
                timestamps["created_at"] = str(row["created_at"])
        row = strategy_to_row(strategy, timestamps=timestamps)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO strategies (
                    strategy_id, name, strategy_type, enabled, parameters_json,
                    symbols_json, state, statistics_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(strategy_id) DO UPDATE SET
                    name = excluded.name,
                    strategy_type = excluded.strategy_type,
                    enabled = excluded.enabled,
                    parameters_json = excluded.parameters_json,
                    symbols_json = excluded.symbols_json,
                    state = excluded.state,
                    statistics_json = excluded.statistics_json,
                    updated_at = excluded.updated_at
                """,
                (
                    row["strategy_id"],
                    row["name"],
                    row["strategy_type"],
                    row["enabled"],
                    row["parameters_json"],
                    row["symbols_json"],
                    row["state"],
                    row["statistics_json"],
                    row["created_at"],
                    row["updated_at"],
                ),
            )

    def get(self, strategy_id: str) -> Strategy | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM strategies WHERE strategy_id = ?",
                (strategy_id,),
            ).fetchone()
        data = self._row_to_dict(row)
        return row_to_strategy(data) if data else None

    def list_all(self) -> list[Strategy]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM strategies ORDER BY name").fetchall()
        return [row_to_strategy(dict(row)) for row in rows]

    def delete(self, strategy_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM strategies WHERE strategy_id = ?",
                (strategy_id,),
            )
        return cursor.rowcount > 0
