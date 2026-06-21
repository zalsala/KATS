"""Plugin validation rules."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.plugins.base_indicator import BaseIndicator
from app.plugins.base_notification import BaseNotification
from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_types import PluginType
from app.strategy.base_strategy import BaseStrategy

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "app.broker",
    "app.service.websocket",
    "app.service.order",
    "app.config.config_manager",
    "app.config.app_settings",
)

FORBIDDEN_IMPORT_MODULES: frozenset[str] = frozenset(
    {
        "requests",
        "httpx",
        "aiohttp",
        "websockets",
        "websocket",
    }
)


@dataclass(frozen=True, slots=True)
class PluginValidationResult:
    """Outcome of plugin manifest and module validation."""

    valid: bool
    errors: tuple[str, ...] = ()


class PluginValidator:
    """Validates plugin manifests and source modules before loading."""

    def validate_manifest_file(self, manifest_path: Path) -> PluginValidationResult:
        """Validate that a plugin.json file exists and parses."""
        if not manifest_path.is_file():
            return PluginValidationResult(valid=False, errors=("plugin.json not found",))
        try:
            manifest = PluginManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - convert to validation errors
            return PluginValidationResult(valid=False, errors=(f"Invalid manifest: {exc}",))
        return self.validate_manifest(manifest, plugin_dir=manifest_path.parent)

    def validate_manifest(
        self,
        manifest: PluginManifest,
        *,
        plugin_dir: Path,
    ) -> PluginValidationResult:
        """Validate manifest fields and expected entry point file."""
        errors: list[str] = []
        entry_path = (plugin_dir / manifest.entry_point).resolve()
        plugin_root = plugin_dir.resolve()
        if plugin_root not in entry_path.parents and entry_path != plugin_root:
            errors.append("entry_point must stay inside plugin directory")
        if not entry_path.is_file():
            errors.append(f"entry_point not found: {manifest.entry_point}")

        if manifest.type == PluginType.STRATEGY and not manifest.resolve_registration_key():
            errors.append("strategy plugin requires strategy_type or id")
        if manifest.type == PluginType.INDICATOR and not manifest.resolve_registration_key():
            errors.append("indicator plugin requires indicator_name or id")
        if manifest.type == PluginType.NOTIFICATION and not manifest.resolve_registration_key():
            errors.append("notification plugin requires notification_channel or id")

        if entry_path.is_file():
            import_errors = self.validate_forbidden_imports(entry_path)
            errors.extend(import_errors)

        if errors:
            return PluginValidationResult(valid=False, errors=tuple(errors))
        return PluginValidationResult(valid=True)

    def validate_forbidden_imports(self, source_path: Path) -> list[str]:
        """Reject modules that import forbidden infrastructure layers."""
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_path))
        errors: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    errors.extend(self._check_import(alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                errors.extend(self._check_import(node.module))
        return errors

    def validate_plugin_class(
        self,
        manifest: PluginManifest,
        plugin_class: type[Any],
    ) -> PluginValidationResult:
        """Validate that the loaded class matches the declared plugin type."""
        errors: list[str] = []
        if manifest.type == PluginType.STRATEGY and not issubclass(plugin_class, BaseStrategy):
            errors.append(f"{manifest.class_name} must inherit BaseStrategy")
        if manifest.type == PluginType.INDICATOR and not issubclass(plugin_class, BaseIndicator):
            errors.append(f"{manifest.class_name} must inherit BaseIndicator")
        if manifest.type == PluginType.NOTIFICATION and not issubclass(
            plugin_class, BaseNotification
        ):
            errors.append(f"{manifest.class_name} must inherit BaseNotification")

        if errors:
            return PluginValidationResult(valid=False, errors=tuple(errors))
        return PluginValidationResult(valid=True)

    def _check_import(self, module_name: str) -> list[str]:
        if module_name in FORBIDDEN_IMPORT_MODULES:
            return [f"Forbidden import: {module_name}"]
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            if module_name == prefix or module_name.startswith(f"{prefix}."):
                return [f"Forbidden import: {module_name}"]
        return []
