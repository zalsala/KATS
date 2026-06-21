"""Strategy lifecycle state."""

from __future__ import annotations

from enum import StrEnum


class StrategyState(StrEnum):
    """Lifecycle states for a strategy."""

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    DISPOSED = "disposed"
