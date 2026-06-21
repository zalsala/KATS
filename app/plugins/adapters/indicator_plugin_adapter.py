"""Indicator plugin adapter."""

from __future__ import annotations

from app.plugins.indicator_registry import IndicatorRegistry
from app.plugins.plugin_registry import LoadedPlugin


class IndicatorPluginAdapter:
    """Register external indicator plugins with IndicatorRegistry."""

    def adapt(self, plugin: LoadedPlugin, indicator_registry: IndicatorRegistry) -> str:
        """Register a loaded indicator plugin factory."""
        indicator_name = plugin.manifest.resolve_registration_key()
        indicator_registry.register(indicator_name, plugin.plugin_class)
        return indicator_name
