"""Plugin validation tests."""

from __future__ import annotations

import pytest
from tests.fixtures.plugin_fixtures import plugin_fixtures_root

from app.plugins.plugin_validator import PluginValidator

pytestmark = pytest.mark.unit


def test_validator_rejects_missing_entry_point() -> None:
    validator = PluginValidator()
    plugin_dir = plugin_fixtures_root() / "strategies" / "invalid_manifest"
    result = validator.validate_manifest_file(plugin_dir / "plugin.json")
    assert result.valid is False
    assert any("name" in error.lower() or "entry_point" in error for error in result.errors)


def test_validator_rejects_forbidden_imports() -> None:
    validator = PluginValidator()
    plugin_dir = plugin_fixtures_root() / "strategies" / "forbidden_import"
    source_path = plugin_dir / "strategy.py"
    errors = validator.validate_forbidden_imports(source_path)
    assert any("order" in error.lower() for error in errors)
