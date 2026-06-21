"""Basic performance logging tests."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app.config.config_models import LoggingConfig
from app.core.logging import LogCategory, setup_logging
from app.core.logging.correlation import CorrelationContext
from app.core.logging.performance import PerformanceLogger

pytestmark = pytest.mark.unit


class TestPerformanceLogger:
    """Tests for PerformanceLogger latency measurement."""

    @pytest.fixture
    def perf_logger(self, tmp_path: Path) -> PerformanceLogger:
        """Return a configured PerformanceLogger."""
        config = LoggingConfig(
            level="INFO",
            structured=True,
            file_output=True,
            console_output=False,
        )
        service = setup_logging(config, tmp_path / "logs")
        return service.get_performance_logger(LogCategory.API)

    def test_measure_logs_latency(self, perf_logger: PerformanceLogger, tmp_path: Path) -> None:
        """measure() logs elapsed time to the API log file."""
        with (
            CorrelationContext("perf-cid-001"),
            perf_logger.measure("kis.rest.get_balance", symbol="005930"),
        ):
            time.sleep(0.01)

        api_log = (tmp_path / "logs" / "api.log").read_text(encoding="utf-8")
        entry = json.loads(api_log.strip())

        assert entry["operation"] == "kis.rest.get_balance"
        assert entry["latency_ms"] >= 10.0
        assert entry["status"] == "ok"
        assert entry["symbol"] == "005930"
        assert entry["correlation_id"] == "perf-cid-001"

    def test_measure_logs_error_status(
        self, perf_logger: PerformanceLogger, tmp_path: Path
    ) -> None:
        """measure() records error status when an exception occurs."""
        with pytest.raises(ValueError), perf_logger.measure("kis.rest.place_order"):
            raise ValueError("Order rejected")

        api_log = (tmp_path / "logs" / "api.log").read_text(encoding="utf-8")
        entry = json.loads(api_log.strip())

        assert entry["status"] == "error"
        assert entry["operation"] == "kis.rest.place_order"

    def test_log_latency_direct(self, perf_logger: PerformanceLogger, tmp_path: Path) -> None:
        """log_latency() emits a structured entry directly."""
        perf_logger.log_latency("kis.rest.cancel_order", 15.5, order_id="ORD001")

        api_log = (tmp_path / "logs" / "api.log").read_text(encoding="utf-8")
        entry = json.loads(api_log.strip())

        assert entry["latency_ms"] == 15.5
        assert entry["order_id"] == "ORD001"

    def test_measure_overhead_is_acceptable(self, perf_logger: PerformanceLogger) -> None:
        """Performance logger overhead for empty operations is under 5ms."""
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            with perf_logger.measure("kis.rest.ping"):
                pass
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        avg_ms = elapsed_ms / iterations

        assert avg_ms < 5.0, f"Average overhead {avg_ms:.2f}ms exceeds 5ms threshold"
