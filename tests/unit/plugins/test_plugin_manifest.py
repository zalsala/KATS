"""Plugin manifest tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_types import PluginType

pytestmark = pytest.mark.unit


def test_manifest_parses_valid_strategy_plugin() -> None:
    manifest_path = plugin_fixtures_root() / "strategies" / "hold_once" / "plugin.json"
    manifest = PluginManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    assert manifest.id == "hold_once"
    assert manifest.type == PluginType.STRATEGY
    assert manifest.resolve_registration_key() == "hold_once"


def test_manifest_rejects_empty_name() -> None:
    payload = {
        "id": "bad",
        "name": "",
        "version": "1.0.0",
        "type": "strategy",
        "entry_point": "strategy.py",
        "class_name": "BadStrategy",
    }
    with pytest.raises(ValidationError):
        PluginManifest.model_validate(payload)


def test_manifest_resolve_registration_key_uses_fallback_id() -> None:
    manifest = PluginManifest(
        id="indicator_fallback",
        name="Fallback",
        version="1.0.0",
        type=PluginType.INDICATOR,
        entry_point="indicator.py",
        class_name="FallbackIndicator",
    )
    assert manifest.resolve_registration_key() == "indicator_fallback"
