"""Shared plugin test fixtures."""

from __future__ import annotations

from pathlib import Path


def plugin_fixtures_root() -> Path:
    """Return the root directory containing test plugin packages."""
    return Path(__file__).resolve().parent / "plugins"
