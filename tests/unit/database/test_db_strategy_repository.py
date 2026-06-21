"""SQLite strategy repository tests."""

from __future__ import annotations

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_state import StrategyState

pytestmark = pytest.mark.unit


def test_strategy_repository_save_and_list(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_strategy_repository()
    strategy = Strategy(
        strategy_id="strategy-1",
        name="template-1",
        strategy_type="template",
        enabled=True,
        parameters={"quantity": "1"},
        symbols=("005930",),
        state=StrategyState.RUNNING,
    )
    repository.save(strategy)
    loaded = repository.get("strategy-1")
    assert loaded is not None
    assert loaded.state == StrategyState.RUNNING
    assert repository.list_all()[0].name == "template-1"
