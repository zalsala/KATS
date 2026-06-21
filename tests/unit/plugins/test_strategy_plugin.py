"""Strategy plugin tests."""

from __future__ import annotations

import pytest
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.plugins.plugin_manager import PluginManager
from app.strategy.strategy_registry import StrategyRegistry

pytestmark = pytest.mark.unit


def test_strategy_plugin_registers_with_strategy_registry() -> None:
    strategy_registry = StrategyRegistry()
    manager = PluginManager(
        plugins_root=plugin_fixtures_root(),
        strategy_registry=strategy_registry,
    )
    report = manager.load_strategy_plugins()
    assert "hold_once" in report.loaded
    assert strategy_registry.is_registered("hold_once")
