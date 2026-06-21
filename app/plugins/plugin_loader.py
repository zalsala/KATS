"""Plugin discovery and module loading."""

from __future__ import annotations

import importlib.util
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_types import MANIFEST_FILENAME, PLUGIN_SUBDIRECTORIES, PluginType
from app.plugins.plugin_validator import PluginValidator


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DiscoveredPlugin:
    """A plugin directory discovered under plugins/."""

    plugin_dir: Path
    manifest_path: Path


class PluginLoader:
    """Discovers plugin packages and loads manifest/module pairs."""

    def __init__(self, *, validator: PluginValidator | None = None) -> None:
        self._validator = validator or PluginValidator()
        self._logger = _resolve_logger()

    def discover(self, plugins_root: Path) -> list[DiscoveredPlugin]:
        """Find plugin directories containing plugin.json under plugins/."""
        discovered: list[DiscoveredPlugin] = []
        if not plugins_root.is_dir():
            return discovered

        for plugin_type in PluginType:
            type_dir = plugins_root / PLUGIN_SUBDIRECTORIES[plugin_type]
            if not type_dir.is_dir():
                continue
            for plugin_dir in sorted(path for path in type_dir.iterdir() if path.is_dir()):
                manifest_path = plugin_dir / MANIFEST_FILENAME
                if manifest_path.is_file():
                    discovered.append(
                        DiscoveredPlugin(plugin_dir=plugin_dir, manifest_path=manifest_path)
                    )
        return discovered

    def load_manifest(self, manifest_path: Path) -> PluginManifest | None:
        """Parse plugin.json into a manifest model."""
        result = self._validator.validate_manifest_file(manifest_path)
        if not result.valid:
            for error in result.errors:
                self._logger.warning("Plugin manifest rejected at %s: %s", manifest_path, error)
            return None
        return PluginManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    def load_plugin_class(
        self,
        *,
        plugin_dir: Path,
        manifest: PluginManifest,
    ) -> type[Any] | None:
        """Import the plugin module and return the declared class."""
        manifest_result = self._validator.validate_manifest(manifest, plugin_dir=plugin_dir)
        if not manifest_result.valid:
            for error in manifest_result.errors:
                self._logger.warning(
                    "Plugin validation failed for %s: %s",
                    manifest.id,
                    error,
                )
            return None

        entry_path = plugin_dir / manifest.entry_point
        module_name = f"kats_plugin_{manifest.type}_{manifest.id}".replace("-", "_")
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        if spec is None or spec.loader is None:
            self._logger.warning("Unable to create import spec for plugin %s", manifest.id)
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:  # noqa: BLE001 - plugin errors must not crash the app
            self._logger.exception("Plugin module execution failed for %s", manifest.id)
            return None

        plugin_class = getattr(module, manifest.class_name, None)
        if plugin_class is None:
            self._logger.warning(
                "Plugin class %s not found in %s",
                manifest.class_name,
                manifest.entry_point,
            )
            return None

        typed_class = cast(type[Any], plugin_class)
        class_result = self._validator.validate_plugin_class(manifest, typed_class)
        if not class_result.valid:
            for error in class_result.errors:
                self._logger.warning("Plugin class rejected for %s: %s", manifest.id, error)
            return None
        return typed_class
