"""Plugin loader tests."""

from __future__ import annotations

import pytest
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.plugins.plugin_loader import PluginLoader

pytestmark = pytest.mark.unit


def test_loader_discovers_fixture_plugins() -> None:
    loader = PluginLoader()
    discovered = loader.discover(plugin_fixtures_root())
    plugin_names = {item.plugin_dir.name for item in discovered}
    assert "hold_once" in plugin_names
    assert "double_sma" in plugin_names
    assert "console_notifier" in plugin_names


def test_loader_loads_valid_strategy_class() -> None:
    loader = PluginLoader()
    plugin_dir = plugin_fixtures_root() / "strategies" / "hold_once"
    manifest = loader.load_manifest(plugin_dir / "plugin.json")
    assert manifest is not None
    plugin_class = loader.load_plugin_class(plugin_dir=plugin_dir, manifest=manifest)
    assert plugin_class is not None
    assert plugin_class.strategy_type == "hold_once"
