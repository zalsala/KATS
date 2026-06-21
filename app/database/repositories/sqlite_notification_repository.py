"""SQLite notification repository."""

from __future__ import annotations

from app.database.base_repository import BaseRepository
from app.database.repository_mappers import notification_to_row, row_to_notification
from app.notification.notification_message import NotificationMessage


class SQLiteNotificationRepository(BaseRepository):
    """SQLite-backed notification history persistence."""

    def save(self, message: NotificationMessage) -> None:
        row = notification_to_row(message)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO notifications (
                    notification_id, category, title, body, level,
                    source_event, context_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(notification_id) DO UPDATE SET
                    category = excluded.category,
                    title = excluded.title,
                    body = excluded.body,
                    level = excluded.level,
                    source_event = excluded.source_event,
                    context_json = excluded.context_json,
                    created_at = excluded.created_at
                """,
                (
                    row["notification_id"],
                    row["category"],
                    row["title"],
                    row["body"],
                    row["level"],
                    row["source_event"],
                    row["context_json"],
                    row["created_at"],
                ),
            )

    def get(self, notification_id: str) -> NotificationMessage | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM notifications WHERE notification_id = ?",
                (notification_id,),
            ).fetchone()
        data = self._row_to_dict(row)
        return row_to_notification(data) if data else None

    def list_all(self, *, limit: int = 500) -> list[NotificationMessage]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [row_to_notification(dict(row)) for row in rows]
