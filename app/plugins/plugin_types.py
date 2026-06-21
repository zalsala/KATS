"""Plugin type definitions."""

from __future__ import annotations

from enum import StrEnum


class PluginType(StrEnum):
    """Supported external plugin categories."""

    STRATEGY = "strategy"
    INDICATOR = "indicator"
    NOTIFICATION = "notification"


PLUGIN_SUBDIRECTORIES: dict[PluginType, str] = {
    PluginType.STRATEGY: "strategies",
    PluginType.INDICATOR: "indicators",
    PluginType.NOTIFICATION: "notifications",
}

MANIFEST_FILENAME = "plugin.json"
