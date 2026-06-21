"""Base event model for KATS EventBus."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging.correlation import generate_correlation_id, resolve_correlation_id
from app.events.event_types import EventType


@dataclass(slots=True)
class BaseEvent:
    """Base class for all domain events.

    Attributes:
        event_type: Event category.
        source: Publishing module name.
        payload: Event-specific data dictionary.
        event_id: Unique event identifier.
        event_name: Human-readable event name.
        occurred_at: UTC timestamp when the event was created.
        correlation_id: Trace identifier shared across a workflow.
    """

    event_type: EventType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_name: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = field(default_factory=resolve_correlation_id)

    def __post_init__(self) -> None:
        if not self.event_name:
            self.event_name = self.event_type.value
        if self.correlation_id == "-":
            self.correlation_id = generate_correlation_id()
