"""Unit tests for log formatters."""

from __future__ import annotations

import json
import logging

import pytest

from app.core.logging.constants import CORRELATION_ID_FIELD
from app.core.logging.correlation import CorrelationContext
from app.core.logging.formatters import JsonLogFormatter, TextLogFormatter

pytestmark = pytest.mark.unit


class TestTextLogFormatter:
    """Tests for TextLogFormatter."""

    def test_includes_correlation_id(self) -> None:
        """Text formatter includes correlation ID in output."""
        formatter = TextLogFormatter()
        record = logging.LogRecord(
            name="kats.api.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with CorrelationContext("cid-text-001"):
            output = formatter.format(record)

        assert "cid-text-001" in output
        assert "Test message" in output


class TestJsonLogFormatter:
    """Tests for JsonLogFormatter."""

    def test_outputs_valid_json(self) -> None:
        """JSON formatter produces parseable structured output."""
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="kats.api.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="API call completed",
            args=(),
            exc_info=None,
        )

        with CorrelationContext("cid-json-001"):
            output = formatter.format(record)

        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "API call completed"
        assert data[CORRELATION_ID_FIELD] == "cid-json-001"
        assert "timestamp" in data

    def test_includes_extra_fields(self) -> None:
        """JSON formatter includes custom extra fields."""
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="kats.api.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Latency recorded",
            args=(),
            exc_info=None,
        )
        record.latency_ms = 42.5  # type: ignore[attr-defined]
        record.operation = "kis.rest.get_balance"  # type: ignore[attr-defined]

        output = formatter.format(record)
        data = json.loads(output)

        assert data["latency_ms"] == 42.5
        assert data["operation"] == "kis.rest.get_balance"

    def test_masks_secrets_in_json_message(self) -> None:
        """JSON formatter masks secrets in the message field."""
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="kats.api.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="app_key=SECRET123456",
            args=(),
            exc_info=None,
        )

        data = json.loads(formatter.format(record))

        assert "SECRET123456" not in data["message"]
