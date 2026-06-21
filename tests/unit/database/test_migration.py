"""Migration tests."""

from __future__ import annotations

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

pytestmark = pytest.mark.unit


def test_migration_applies_initial_schema(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    applied = manager.migration_manager.list_applied()
    assert "001_initial" in applied


def test_migration_is_idempotent(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    first = manager.migration_manager.migrate()
    second = manager.migration_manager.migrate()
    assert first == []
    assert second == []
