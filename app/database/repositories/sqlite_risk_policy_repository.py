"""SQLite risk policy repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import risk_policy_to_row, row_to_risk_policy
from app.domain.risk.risk_policy import RiskPolicy


class SQLiteRiskPolicyRepository(BaseRepository):
    """SQLite-backed risk policy persistence."""

    def save(self, policy: RiskPolicy, *, policy_name: str = "default") -> None:
        row = risk_policy_to_row(policy, policy_name=policy_name)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO risk_policies (
                    policy_name, max_order_amount, max_order_quantity, max_position_count,
                    max_symbol_weight, daily_loss_limit, duplicate_order_block,
                    emergency_stop, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_name) DO UPDATE SET
                    max_order_amount = excluded.max_order_amount,
                    max_order_quantity = excluded.max_order_quantity,
                    max_position_count = excluded.max_position_count,
                    max_symbol_weight = excluded.max_symbol_weight,
                    daily_loss_limit = excluded.daily_loss_limit,
                    duplicate_order_block = excluded.duplicate_order_block,
                    emergency_stop = excluded.emergency_stop,
                    updated_at = excluded.updated_at
                """,
                (
                    row["policy_name"],
                    row["max_order_amount"],
                    row["max_order_quantity"],
                    row["max_position_count"],
                    row["max_symbol_weight"],
                    row["daily_loss_limit"],
                    row["duplicate_order_block"],
                    row["emergency_stop"],
                    row["updated_at"],
                ),
            )

    def get(self, policy_name: str = "default") -> RiskPolicy | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM risk_policies WHERE policy_name = ?",
                (policy_name,),
            ).fetchone()
        data = self._row_to_dict(row)
        return row_to_risk_policy(data) if data else None

    def list_all(self) -> list[tuple[str, RiskPolicy]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM risk_policies ORDER BY policy_name").fetchall()
        return [(str(row["policy_name"]), row_to_risk_policy(dict(row))) for row in rows]
