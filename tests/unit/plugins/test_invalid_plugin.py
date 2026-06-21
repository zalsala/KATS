"""Invalid plugin handling tests."""

from __future__ import annotations

import pytest
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.plugins.plugin_manager import PluginManager
from app.strategy.strategy_registry import StrategyRegistry

pytestmark = pytest.mark.unit


def test_invalid_plugins_are_skipped_without_crashing() -> None:
    strategy_registry = StrategyRegistry()
    manager = PluginManager(
        plugins_root=plugin_fixtures_root(),
        strategy_registry=strategy_registry,
    )
    report = manager.load_all()
    assert "hold_once" in report.loaded
    assert "invalid_manifest" in report.skipped or "forbidden_import" in report.skipped
    assert strategy_registry.is_registered("hold_once") is True
    assert strategy_registry.is_registered("forbidden_strategy") is False
