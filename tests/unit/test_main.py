"""Smoke tests for application entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
from main import main

from app.config.config_manager import ConfigManager


@pytest.mark.unit
class TestMain:
    """Tests for main entry point."""

    def test_main_returns_zero(self, project_root: Path) -> None:
        """Application starts successfully and returns exit code 0."""
        ConfigManager.get_instance(project_root=project_root, environment="development")

        assert main([]) == 0
