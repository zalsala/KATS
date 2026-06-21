"""Plugin loading orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.plugins.adapters.indicator_plugin_adapter import IndicatorPluginAdapter
from app.plugins.adapters.notification_plugin_adapter import NotificationPluginAdapter
from app.plugins.adapters.strategy_plugin_adapter import StrategyPluginAdapter
from app.plugins.indicator_registry import IndicatorRegistry
from app.plugins.notification_registry import NotificationRegistry
from app.plugins.plugin_loader import PluginLoader
from app.plugins.plugin_registry import LoadedPlugin, PluginRegistry
from app.plugins.plugin_types import PluginType
from app.plugins.plugin_validator import PluginValidator
from app.strategy.strategy_registry import StrategyRegistry


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


@dataclass(slots=True)
class PluginLoadReport:
    """Summary of a plugin loading pass."""

    loaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def loaded_count(self) -> int:
        return len(self.loaded)


class PluginManager:
    """Discover, validate, load, and adapt external plugins."""

    def __init__(
        self,
        *,
        plugins_root: Path,
        plugin_registry: PluginRegistry | None = None,
        strategy_registry: StrategyRegistry | None = None,
        indicator_registry: IndicatorRegistry | None = None,
        notification_registry: NotificationRegistry | None = None,
        loader: PluginLoader | None = None,
        strategy_adapter: StrategyPluginAdapter | None = None,
        indicator_adapter: IndicatorPluginAdapter | None = None,
        notification_adapter: NotificationPluginAdapter | None = None,
    ) -> None:
        self._plugins_root = plugins_root
        self._plugin_registry = plugin_registry or PluginRegistry()
        self._strategy_registry = strategy_registry
        self._indicator_registry = indicator_registry or IndicatorRegistry()
        self._notification_registry = notification_registry or NotificationRegistry()
        self._loader = loader or PluginLoader(validator=PluginValidator())
        self._strategy_adapter = strategy_adapter or StrategyPluginAdapter()
        self._indicator_adapter = indicator_adapter or IndicatorPluginAdapter()
        self._notification_adapter = notification_adapter or NotificationPluginAdapter()
        self._logger = _resolve_logger()

    @property
    def plugin_registry(self) -> PluginRegistry:
        return self._plugin_registry

    @property
    def indicator_registry(self) -> IndicatorRegistry:
        return self._indicator_registry

    @property
    def notification_registry(self) -> NotificationRegistry:
        return self._notification_registry

    def load_all(self) -> PluginLoadReport:
        """Load every discovered plugin under plugins/."""
        report = PluginLoadReport()
        for discovered in self._loader.discover(self._plugins_root):
            plugin_id = discovered.plugin_dir.name
            try:
                loaded = self._load_discovered_plugin(
                    discovered.plugin_dir,
                    discovered.manifest_path,
                )
            except Exception as exc:  # noqa: BLE001 - isolate plugin failures
                message = str(exc)
                report.errors.append((plugin_id, message))
                self._logger.exception("Unexpected plugin load failure for %s", plugin_id)
                continue

            if loaded is None:
                report.skipped.append(plugin_id)
                continue

            report.loaded.append(loaded.manifest.id)
        return report

    def load_strategy_plugins(self) -> PluginLoadReport:
        """Load only strategy plugins and adapt them to StrategyRegistry."""
        return self._load_by_type(PluginType.STRATEGY)

    def load_indicator_plugins(self) -> PluginLoadReport:
        """Load only indicator plugins."""
        return self._load_by_type(PluginType.INDICATOR)

    def load_notification_plugins(self) -> PluginLoadReport:
        """Load only notification plugins."""
        return self._load_by_type(PluginType.NOTIFICATION)

    def _load_by_type(self, plugin_type: PluginType) -> PluginLoadReport:
        report = PluginLoadReport()
        for discovered in self._loader.discover(self._plugins_root):
            manifest = self._loader.load_manifest(discovered.manifest_path)
            if manifest is None or manifest.type != plugin_type:
                continue
            loaded = self._load_discovered_plugin(discovered.plugin_dir, discovered.manifest_path)
            if loaded is None:
                report.skipped.append(discovered.plugin_dir.name)
                continue
            report.loaded.append(loaded.manifest.id)
        return report

    def _load_discovered_plugin(
        self,
        plugin_dir: Path,
        manifest_path: Path,
    ) -> LoadedPlugin | None:
        manifest = self._loader.load_manifest(manifest_path)
        if manifest is None:
            return None

        if self._plugin_registry.is_registered(manifest.id):
            self._logger.info("Plugin already loaded: %s", manifest.id)
            return self._plugin_registry.get(manifest.id)

        plugin_class = self._loader.load_plugin_class(plugin_dir=plugin_dir, manifest=manifest)
        if plugin_class is None:
            return None

        loaded = LoadedPlugin(
            manifest=manifest,
            plugin_class=plugin_class,
            plugin_dir=plugin_dir,
        )
        self._plugin_registry.register(loaded)
        self._adapt_plugin(loaded)
        self._logger.info(
            "Loaded plugin id=%s type=%s version=%s",
            manifest.id,
            manifest.type,
            manifest.version,
        )
        return loaded

    def _adapt_plugin(self, plugin: LoadedPlugin) -> None:
        if plugin.manifest.type == PluginType.STRATEGY:
            if self._strategy_registry is None:
                self._logger.warning(
                    "Strategy plugin %s loaded but no StrategyRegistry was provided",
                    plugin.manifest.id,
                )
                return
            self._strategy_adapter.adapt(plugin, self._strategy_registry)
            return
        if plugin.manifest.type == PluginType.INDICATOR:
            self._indicator_adapter.adapt(plugin, self._indicator_registry)
            return
        self._notification_adapter.adapt(plugin, self._notification_registry)


def load_plugins_into_strategy_registry(
    *,
    plugins_root: Path,
    strategy_registry: StrategyRegistry,
) -> PluginLoadReport:
    """Load external strategy plugins into an existing StrategyRegistry."""
    manager = PluginManager(
        plugins_root=plugins_root,
        strategy_registry=strategy_registry,
    )
    return manager.load_all()
