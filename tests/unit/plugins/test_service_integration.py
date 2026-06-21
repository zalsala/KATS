"""StrategyService plugin integration tests."""

from __future__ import annotations

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.service.strategy.strategy_service import build_strategy_service

pytestmark = pytest.mark.unit


def test_service_loads_external_strategy_plugin() -> None:
    service = build_strategy_service(
        event_bus=build_test_event_bus_service(),
        plugins_root=plugin_fixtures_root(),
        load_plugins=True,
    )
    assert service.registry.is_registered("hold_once")
    dto = service.register_strategy(
        strategy_type="hold_once",
        name="hold-once-1",
        symbols=["005930"],
    )
    assert dto.strategy_type == "hold_once"


def test_service_still_supports_builtin_strategies_with_plugins() -> None:
    service = build_strategy_service(
        plugins_root=plugin_fixtures_root(),
        load_plugins=True,
    )
    assert service.registry.is_registered("template")
    assert service.registry.is_registered("hold_once")
