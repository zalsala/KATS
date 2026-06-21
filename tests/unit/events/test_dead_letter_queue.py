"""DeadLetterQueue tests."""

from __future__ import annotations

import pytest

from app.events.dead_letter_queue import DeadLetterQueue
from app.events.domain_events import ErrorEvent

pytestmark = pytest.mark.unit


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue."""

    def test_push_and_all(self) -> None:
        dlq = DeadLetterQueue(max_size=10)
        event = ErrorEvent(source="bus", payload={"reason": "fail"})

        dlq.push(event, handler_name="handler_a", error="boom")

        entries = dlq.all()
        assert len(entries) == 1
        assert entries[0].handler_name == "handler_a"
        assert entries[0].error == "boom"

    def test_clear(self) -> None:
        dlq = DeadLetterQueue()
        dlq.push(ErrorEvent(source="bus"), handler_name="h", error="e")

        dlq.clear()

        assert dlq.size() == 0

    def test_respects_max_size(self) -> None:
        dlq = DeadLetterQueue(max_size=2)

        for index in range(3):
            dlq.push(
                ErrorEvent(source="bus", payload={"index": index}),
                handler_name=f"h{index}",
                error="e",
            )

        assert dlq.size() == 2
        assert dlq.all()[0].event.payload["index"] == 1
