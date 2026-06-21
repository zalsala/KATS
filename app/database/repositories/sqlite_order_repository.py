"""SQLite order repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import order_to_row, row_to_order
from app.domain.order.order import Order


class SQLiteOrderRepository(BaseRepository):
    """SQLite-backed order persistence."""

    def save(self, order: Order) -> None:
        row = order_to_row(order)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO orders (
                    order_number, order_branch, symbol_code, side,
                    quantity, price, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_number) DO UPDATE SET
                    order_branch = excluded.order_branch,
                    symbol_code = excluded.symbol_code,
                    side = excluded.side,
                    quantity = excluded.quantity,
                    price = excluded.price,
                    status = excluded.status
                """,
                (
                    row["order_number"],
                    row["order_branch"],
                    row["symbol_code"],
                    row["side"],
                    row["quantity"],
                    row["price"],
                    row["status"],
                    row["created_at"],
                ),
            )

    def get(self, order_number: str) -> Order | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM orders WHERE order_number = ?",
                (order_number,),
            ).fetchone()
        data = self._row_to_dict(row)
        return row_to_order(data) if data else None

    def list_all(self) -> list[Order]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM orders ORDER BY id").fetchall()
        return [row_to_order(dict(row)) for row in rows]

    def update_status(self, order_number: str, status: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE orders SET status = ? WHERE order_number = ?",
                (status, order_number),
            )
        return cursor.rowcount > 0
