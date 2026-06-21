"""Unit tests for logging setup and LoggerService."""

from __future__ import annotations

import logging

import pytest

from app.config.config_models import LoggingConfig
from app.core.logging import LogCategory, LoggerService, get_logger, setup_logging
from app.core.logging.constants import CATEGORY_LOGGER_NAMES, LOG_ROOT_NAME

pytestmark = pytest.mark.unit


@pytest.fixture
def logging_config() -> LoggingConfig:
    """Return a test logging configuration."""
    return LoggingConfig(
        level="DEBUG",
        structured=False,
        file_output=True,
        console_output=False,
        rotation=True,
        backup_count=3,
    )


class TestLoggerService:
    """Tests for LoggerService setup and logger retrieval."""

    def test_setup_creates_log_directory(
        self,
        tmp_path: object,
        logging_config: LoggingConfig,
    ) -> None:
        """setup_logging creates the logs directory and category files."""
        from pathlib import Path

        logs_dir = Path(str(tmp_path)) / "logs"
        setup_logging(logging_config, logs_dir)

        assert logs_dir.exists()
        assert (logs_dir / "system.log").exists()
        assert (logs_dir / "api.log").exists()

    def test_setup_sets_log_level(self, tmp_path: object, logging_config: LoggingConfig) -> None:
        """setup_logging applies the configured log level."""
        from pathlib import Path

        logging_config = LoggingConfig(level="WARNING", file_output=False, console_output=True)
        setup_logging(logging_config, Path(str(tmp_path)) / "logs")

        assert logging.getLogger(LOG_ROOT_NAME).level == logging.WARNING

    def test_get_logger_requires_setup(self) -> None:
        """get_logger raises when setup has not been called."""
        with pytest.raises(RuntimeError, match="setup"):
            get_logger("test")

    def test_get_logger_returns_category_logger(
        self,
        tmp_path: object,
        logging_config: LoggingConfig,
    ) -> None:
        """get_logger returns a logger under the kats namespace."""
        from pathlib import Path

        setup_logging(logging_config, Path(str(tmp_path)) / "logs")
        api_logger = get_logger("rest_client", category=LogCategory.API)

        assert api_logger.name == f"{CATEGORY_LOGGER_NAMES[LogCategory.API]}.rest_client"

    def test_singleton_returns_same_instance(self, tmp_path: object) -> None:
        """LoggerService.get_instance returns the same object."""
        from pathlib import Path

        config = LoggingConfig(file_output=False, console_output=True)
        first = setup_logging(config, Path(str(tmp_path)) / "logs")
        second = LoggerService.get_instance()

        assert first is second
