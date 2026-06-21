"""Plugin manifest model for plugin.json files."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.plugins.plugin_types import PluginType


class PluginManifest(BaseModel):
    """Metadata describing an external plugin package."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    type: PluginType
    entry_point: str = Field(min_length=1)
    class_name: str = Field(min_length=1)
    description: str = ""
    author: str = ""
    strategy_type: str | None = None
    indicator_name: str | None = None
    notification_channel: str | None = None

    @field_validator("id", "strategy_type", "indicator_name", "notification_channel")
    @classmethod
    def _strip_optional_identifiers(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def resolve_registration_key(self) -> str:
        """Return the registry key used when adapting this plugin."""
        if self.type == PluginType.STRATEGY:
            return self.strategy_type or self.id
        if self.type == PluginType.INDICATOR:
            return self.indicator_name or self.id
        return self.notification_channel or self.id
