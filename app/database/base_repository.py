"""Shared repository helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.database.connection.sqlite_connection_factory import SQLiteConnectionFactory


class BaseRepository:
    """Base class for SQLite repositories."""

    def __init__(self, *, connection_factory: SQLiteConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connection_factory.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}  # noqa: SIM118
