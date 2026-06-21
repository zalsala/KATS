"""Console notification plugin for tests."""

from __future__ import annotations

from typing import Any

from app.plugins.base_notification import BaseNotification


class ConsoleNotifier(BaseNotification):
    """Store the last message in memory for assertions."""

    channel_name = "console"
    last_message: str | None = None

    def send(self, message: str, *, context: dict[str, Any] | None = None) -> bool:
        ConsoleNotifier.last_message = message
        return True
