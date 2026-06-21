"""Mock-based tests for logging handlers and output."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.config_models import LoggingConfig
from app.core.logging import LogCategory, setup_logging
from app.core.logging.correlation import CorrelationContext
from app.core.logging.logger_service import LoggerService

pytestmark = pytest.mark.unit


class TestLoggingMock:
    """Mock-based logging integration tests."""

    def test_console_handler_receives_log_record(self, tmp_path: Path) -> None:
        """Console handler emits formatted log records."""
        stream = StringIO()
        config = LoggingConfig(level="INFO", file_output=False, console_output=True)

        with patch("sys.stdout", stream):
            service = setup_logging(config, tmp_path / "logs")
            logger = service.get_logger("mock_test", category=LogCategory.SYSTEM)

            with CorrelationContext("mock-cid-001"):
                logger.info("Mock console message")

        output = stream.getvalue()
        assert "Mock console message" in output
        assert "mock-cid-001" in output

    def test_api_log_written_to_file(self, tmp_path: Path) -> None:
        """API category logs are written to api.log."""
        config = LoggingConfig(
            level="DEBUG",
            structured=True,
            file_output=True,
            console_output=False,
        )
        service = setup_logging(config, tmp_path / "logs")
        api_logger = service.get_logger("mock_api", category=LogCategory.API)

        with CorrelationContext("mock-cid-api"):
            api_logger.info("KIS REST response received", extra={"status_code": 200})

        api_log = (tmp_path / "logs" / "api.log").read_text(encoding="utf-8")
        assert "KIS REST response received" in api_log

        entry = json.loads(api_log.strip())
        assert entry["correlation_id"] == "mock-cid-api"
        assert entry["status_code"] == 200

    def test_error_log_only_records_error_and_above(self, tmp_path: Path) -> None:
        """error.log receives ERROR and CRITICAL records only."""
        config = LoggingConfig(
            level="DEBUG",
            file_output=True,
            console_output=False,
        )
        service = setup_logging(config, tmp_path / "logs")
        error_logger = service.get_logger("mock_error", category=LogCategory.ERROR)

        error_logger.info("Should not appear in error log")
        error_logger.error("Critical failure detected")

        error_log = (tmp_path / "logs" / "error.log").read_text(encoding="utf-8")
        assert "Critical failure detected" in error_log
        assert "Should not appear" not in error_log

    def test_sensitive_data_masked_in_output(self, tmp_path: Path) -> None:
        """Sensitive values are masked before being written."""
        config = LoggingConfig(file_output=True, console_output=False)
        service = setup_logging(config, tmp_path / "logs")
        logger = service.get_logger("mask_test", category=LogCategory.API)

        logger.info("app_secret=TOP_SECRET_VALUE")

        api_log = (tmp_path / "logs" / "api.log").read_text(encoding="utf-8")
        assert "TOP_SECRET_VALUE" not in api_log

    def test_shutdown_closes_handlers(self, tmp_path: Path) -> None:
        """shutdown() closes all handlers without error."""
        config = LoggingConfig(file_output=True, console_output=True)
        setup_logging(config, tmp_path / "logs")

        LoggerService.get_instance().shutdown()

        assert LoggerService.get_instance().is_configured is False
