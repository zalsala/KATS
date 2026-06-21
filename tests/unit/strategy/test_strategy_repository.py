"""Strategy repository tests."""

from __future__ import annotations

import pytest

from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_state import StrategyState
from app.repository.in_memory_strategy_repository import InMemoryStrategyRepository

pytestmark = pytest.mark.unit


def test_repository_save_and_get() -> None:
    repo = InMemoryStrategyRepository()
    entity = Strategy(
        strategy_id="s1",
        name="test",
        strategy_type="buy_and_hold",
        enabled=True,
        parameters={},
        symbols=("005930",),
        state=StrategyState.CREATED,
    )
    repo.save(entity)
    loaded = repo.get("s1")
    assert loaded is not None
    assert loaded.name == "test"


def test_repository_list_and_delete() -> None:
    repo = InMemoryStrategyRepository()
    entity = Strategy(
        strategy_id="s1",
        name="test",
        strategy_type="template",
        enabled=True,
        parameters={},
        symbols=("005930",),
    )
    repo.save(entity)
    assert len(repo.list_all()) == 1
    assert repo.delete("s1") is True
    assert repo.list_all() == []
