"""In-memory registry for loaded plugins."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_types import PluginType


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """Runtime representation of a successfully loaded plugin."""

    manifest: PluginManifest
    plugin_class: type[Any]
    plugin_dir: Path


class PluginRegistry:
    """Stores loaded plugin metadata and classes by id and type."""

    def __init__(self) -> None:
        self._plugins: dict[str, LoadedPlugin] = {}

    def register(self, plugin: LoadedPlugin) -> None:
        """Register a loaded plugin by manifest id."""
        self._plugins[plugin.manifest.id] = plugin

    def get(self, plugin_id: str) -> LoadedPlugin | None:
        """Return a plugin by manifest id."""
        return self._plugins.get(plugin_id)

    def list_all(self) -> tuple[LoadedPlugin, ...]:
        """Return all loaded plugins."""
        return tuple(self._plugins.values())

    def list_by_type(self, plugin_type: PluginType) -> tuple[LoadedPlugin, ...]:
        """Return loaded plugins filtered by type."""
        return tuple(
            plugin for plugin in self._plugins.values() if plugin.manifest.type == plugin_type
        )

    def is_registered(self, plugin_id: str) -> bool:
        """Return whether a plugin id is registered."""
        return plugin_id in self._plugins
