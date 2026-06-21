"""Plugin runtime wiring for application bootstrap."""

from __future__ import annotations

import logging
from pathlib import Path

from app.plugins.plugin_manager import PluginLoadReport, PluginManager
from app.strategy.default_registry import register_default_strategies
from app.strategy.strategy_registry import StrategyRegistry

logger = logging.getLogger(__name__)


def wire_strategy_plugins(
    *,
    project_root: Path,
    auto_load: bool,
) -> tuple[StrategyRegistry, PluginManager | None, PluginLoadReport | None]:
    """Create a StrategyRegistry and optionally load plugins into it."""
    registry = StrategyRegistry()
    register_default_strategies(registry)

    if not auto_load:
        return registry, None, None

    plugins_root = project_root / "plugins"
    manager = PluginManager(plugins_root=plugins_root, strategy_registry=registry)
    report = manager.load_all()
    _log_plugin_report(report)
    return registry, manager, report


def _log_plugin_report(report: PluginLoadReport) -> None:
    """Log plugin load results without interrupting application startup."""
    for plugin_id, error in report.errors:
        logger.error("Plugin load failed id=%s error=%s", plugin_id, error)
    for plugin_id in report.skipped:
        logger.warning("Plugin skipped id=%s", plugin_id)
    if report.loaded:
        logger.info("Plugins loaded: %s", ", ".join(report.loaded))
