"""SQLite connection tests."""

from __future__ import annotations

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

pytestmark = pytest.mark.unit


def test_connection_factory_opens_database_file(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    with manager.connection_factory.connect() as connection:
        row = connection.execute("SELECT 1 AS value").fetchone()
    assert row is not None
    assert row["value"] == 1
    assert manager.database_path.exists()
