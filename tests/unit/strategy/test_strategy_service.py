"""StrategyService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service

from app.service.strategy.strategy_service import StrategyService, build_strategy_service

pytestmark = pytest.mark.unit


def test_register_and_list_strategies() -> None:
    service = StrategyService()
    service.register_strategy(
        strategy_type="template",
        name="template-1",
        symbols=["005930"],
    )
    strategies = service.list_strategies()
    assert len(strategies) == 1
    assert strategies[0].strategy_type == "template"


def test_start_registers_event_handlers() -> None:
    event_bus = build_test_event_bus_service()
    service = build_strategy_service(event_bus=event_bus)
    service.start(event_bus)
    assert len(service.event_handler.subscription_ids) == 3


def test_start_and_stop_strategy() -> None:
    service = StrategyService()
    dto = service.register_strategy(
        strategy_type="template",
        name="template-1",
        symbols=["005930"],
    )
    started = service.start_strategy(dto.strategy_id)
    assert started.state == "running"
    stopped = service.stop_strategy(dto.strategy_id)
    assert stopped.state == "stopped"
