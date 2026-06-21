"""Strategy plugin adapter."""

from __future__ import annotations

from app.plugins.plugin_registry import LoadedPlugin
from app.strategy.strategy_registry import StrategyRegistry


class StrategyPluginAdapter:
    """Register external strategy plugins with StrategyRegistry."""

    def adapt(self, plugin: LoadedPlugin, strategy_registry: StrategyRegistry) -> str:
        """Register a loaded strategy plugin factory."""
        strategy_type = plugin.manifest.resolve_registration_key()
        strategy_registry.register(strategy_type, plugin.plugin_class)
        return strategy_type
