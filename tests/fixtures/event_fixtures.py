"""Shared fixtures for EventBus tests."""

from __future__ import annotations

from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus


def build_test_event_bus_service() -> EventBusService:
    """Build EventBusService with a fresh in-memory bus."""
    return EventBusService(event_bus=InMemoryEventBus())
