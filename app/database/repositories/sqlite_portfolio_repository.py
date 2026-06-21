"""SQLite portfolio repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import (
    position_to_row,
    row_to_position,
    row_to_snapshot,
    snapshot_to_row,
    utc_now_iso,
)
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.portfolio.position import Position


class SQLitePortfolioRepository(BaseRepository):
    """SQLite-backed portfolio persistence."""

    def save_positions(self, account_no: str, positions: list[Position]) -> None:
        updated_at = utc_now_iso()
        with self._connection() as connection:
            connection.execute("DELETE FROM positions WHERE account_no = ?", (account_no,))
            for position in positions:
                row = position_to_row(position, account_no=account_no, updated_at=updated_at)
                connection.execute(
                    """
                    INSERT INTO positions (
                        account_no, symbol_code, stock_name, quantity,
                        average_price, current_price, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["account_no"],
                        row["symbol_code"],
                        row["stock_name"],
                        row["quantity"],
                        row["average_price"],
                        row["current_price"],
                        row["updated_at"],
                    ),
                )

    def list_positions(self, account_no: str) -> list[Position]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM positions WHERE account_no = ? ORDER BY symbol_code",
                (account_no,),
            ).fetchall()
        return [row_to_position(dict(row)) for row in rows]

    def save_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        row = snapshot_to_row(snapshot)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO portfolio_snapshots (
                    account_no, total_asset, total_evaluation, total_profit_loss,
                    profit_rate, cash_total, cash_orderable, position_count,
                    snapshot_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["account_no"],
                    row["total_asset"],
                    row["total_evaluation"],
                    row["total_profit_loss"],
                    row["profit_rate"],
                    row["cash_total"],
                    row["cash_orderable"],
                    row["position_count"],
                    row["snapshot_json"],
                    row["created_at"],
                ),
            )
            return int(cursor.lastrowid or 0)

    def list_snapshots(self, account_no: str, *, limit: int = 50) -> list[PortfolioSnapshot]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM portfolio_snapshots
                WHERE account_no = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (account_no, limit),
            ).fetchall()
        return [row_to_snapshot(dict(row)) for row in rows]

    def get_latest_snapshot(self, account_no: str) -> PortfolioSnapshot | None:
        snapshots = self.list_snapshots(account_no, limit=1)
        return snapshots[0] if snapshots else None
