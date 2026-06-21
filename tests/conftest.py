"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.config_manager import ConfigManager
from app.core.logging.logger_service import LoggerService


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singletons between tests."""
    ConfigManager.reset_instance()
    LoggerService.reset_instance()
    yield
    ConfigManager.reset_instance()
    LoggerService.reset_instance()


@pytest.fixture
def project_root() -> Path:
    """Return the KATS project root directory."""
    return Path(__file__).resolve().parents[1]
