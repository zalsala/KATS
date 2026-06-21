"""SQLite backtest repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import backtest_to_row, row_to_backtest
from app.domain.backtest.backtest_result import BacktestResult


class SQLiteBacktestRepository(BaseRepository):
    """SQLite-backed backtest result persistence."""

    def save(
        self,
        result: BacktestResult,
        *,
        strategy_type: str,
        strategy_name: str,
        symbols: list[str],
    ) -> int:
        row = backtest_to_row(
            result,
            strategy_type=strategy_type,
            strategy_name=strategy_name,
            symbols=symbols,
        )
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO backtest_results (
                    strategy_type, strategy_name, symbols_json, initial_capital, final_asset,
                    total_return_rate, win_rate, profit_loss_ratio, profit_factor, max_drawdown,
                    trade_count, average_profit, average_loss, equity_curve_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["strategy_type"],
                    row["strategy_name"],
                    row["symbols_json"],
                    row["initial_capital"],
                    row["final_asset"],
                    row["total_return_rate"],
                    row["win_rate"],
                    row["profit_loss_ratio"],
                    row["profit_factor"],
                    row["max_drawdown"],
                    row["trade_count"],
                    row["average_profit"],
                    row["average_loss"],
                    row["equity_curve_json"],
                    row["created_at"],
                ),
            )
            return int(cursor.lastrowid or 0)

    def get(self, result_id: int) -> BacktestResult | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM backtest_results WHERE id = ?",
                (result_id,),
            ).fetchone()
        data = self._row_to_dict(row)
        return row_to_backtest(data) if data else None

    def list_all(self, *, limit: int = 50) -> list[tuple[int, BacktestResult]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM backtest_results ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [(int(row["id"]), row_to_backtest(dict(row))) for row in rows]
