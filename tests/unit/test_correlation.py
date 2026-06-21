"""Unit tests for correlation ID management."""

from __future__ import annotations

import threading

import pytest

from app.core.logging.correlation import (
    CorrelationContext,
    generate_correlation_id,
    get_correlation_id,
    resolve_correlation_id,
)

pytestmark = pytest.mark.unit


class TestCorrelationId:
    """Tests for correlation ID context."""

    def test_generate_correlation_id_has_prefix(self) -> None:
        """Generated IDs use the kats- prefix."""
        cid = generate_correlation_id()

        assert cid.startswith("kats-")
        assert len(cid) > 10

    def test_context_manager_sets_and_resets(self) -> None:
        """CorrelationContext binds and restores correlation ID."""
        assert get_correlation_id() is None

        with CorrelationContext("test-cid-123") as cid:
            assert cid == "test-cid-123"
            assert get_correlation_id() == "test-cid-123"

        assert get_correlation_id() is None

    def test_resolve_returns_placeholder_when_unset(self) -> None:
        """resolve_correlation_id returns '-' when no ID is bound."""
        assert resolve_correlation_id() == "-"

    def test_nested_contexts(self) -> None:
        """Nested contexts restore outer correlation ID correctly."""
        with CorrelationContext("outer") as outer_cid:
            assert get_correlation_id() == outer_cid
            with CorrelationContext("inner") as inner_cid:
                assert get_correlation_id() == inner_cid
            assert get_correlation_id() == outer_cid

    def test_thread_isolation(self) -> None:
        """Correlation IDs are isolated per thread."""
        results: dict[str, str | None] = {}

        def worker(name: str) -> None:
            with CorrelationContext(f"cid-{name}"):
                results[name] = get_correlation_id()

        threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len({results[k] for k in results}) == 3
