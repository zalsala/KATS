"""Base notification interface for plugin notifications."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseNotification(ABC):
    """Abstract base class for notification plugins."""

    channel_name: str = "base"

    @abstractmethod
    def send(self, message: str, *, context: dict[str, Any] | None = None) -> bool:
        """Deliver a notification message."""
