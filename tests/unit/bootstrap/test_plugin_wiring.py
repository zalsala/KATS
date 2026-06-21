"""Plugin runtime wiring tests for FINAL-03."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.fixtures.integration_fixtures import build_integration_context, prepare_integration_root
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.bootstrap.health_check import HealthCheck, _plugin_health
from app.bootstrap.plugin_wiring import wire_strategy_plugins

pytestmark = pytest.mark.unit


def _copy_plugin_fixtures(root: Path) -> None:
    shutil.copytree(plugin_fixtures_root(), root / "plugins")


class TestPluginWiring:
    """PluginManager and StrategyRegistry runtime connection."""

    def test_plugin_manager_wiring_registers_strategies(self, tmp_path) -> None:
        _copy_plugin_fixtures(tmp_path)
        registry, manager, report = wire_strategy_plugins(
            project_root=tmp_path,
            auto_load=True,
        )

        assert manager is not None
        assert report is not None
        assert "hold_once" in report.loaded
        assert registry.is_registered("hold_once")

    def test_strategy_plugin_auto_load(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)

        assert context.plugin_manager is not None
        assert context.plugin_load_report is not None
        assert "example_hold_once" in context.plugin_load_report.loaded
        assert context.strategy_service.registry.is_registered("example_hold_once")

    def test_invalid_plugins_are_skipped_without_crashing(self, tmp_path) -> None:
        _copy_plugin_fixtures(tmp_path)
        registry, _manager, report = wire_strategy_plugins(
            project_root=tmp_path,
            auto_load=True,
        )

        assert report is not None
        assert "hold_once" in report.loaded
        assert "invalid_manifest" in report.skipped or "forbidden_import" in report.skipped
        assert registry.is_registered("hold_once")
        assert registry.is_registered("forbidden_strategy") is False

    def test_auto_load_disabled_skips_plugin_manager(self, project_root) -> None:
        registry, manager, report = wire_strategy_plugins(
            project_root=project_root,
            auto_load=False,
        )

        assert manager is None
        assert report is None
        assert registry.is_registered("buy_and_hold") is True


class TestPluginHealthCheck:
    """HealthCheck plugin status reporting."""

    def test_health_check_plugin_status(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)
        context.start()

        result = HealthCheck().run(context)
        plugins_item = next(item for item in result.items if item.name == "plugins")

        assert plugins_item.healthy is True
        assert "loaded=" in plugins_item.detail
        assert context.plugin_load_report is not None
        assert len(context.plugin_load_report.loaded) >= 1

    def test_plugin_health_when_auto_load_disabled(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)
        context.settings.config.strategy.auto_load = False

        healthy, detail = _plugin_health(context)

        assert healthy is True
        assert detail == "auto_load=false"
