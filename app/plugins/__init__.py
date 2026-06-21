"""External plugin system for KATS."""

from app.plugins.base_indicator import BaseIndicator
from app.plugins.base_notification import BaseNotification
from app.plugins.indicator_registry import IndicatorRegistry
from app.plugins.notification_registry import NotificationRegistry
from app.plugins.plugin_loader import PluginLoader
from app.plugins.plugin_manager import (
    PluginLoadReport,
    PluginManager,
    load_plugins_into_strategy_registry,
)
from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_registry import LoadedPlugin, PluginRegistry
from app.plugins.plugin_types import PluginType
from app.plugins.plugin_validator import PluginValidationResult, PluginValidator

__all__ = [
    "BaseIndicator",
    "BaseNotification",
    "IndicatorRegistry",
    "LoadedPlugin",
    "NotificationRegistry",
    "PluginLoadReport",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginRegistry",
    "PluginType",
    "PluginValidationResult",
    "PluginValidator",
    "load_plugins_into_strategy_registry",
]
