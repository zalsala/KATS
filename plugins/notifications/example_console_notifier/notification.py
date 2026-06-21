"""Example console notification plugin."""

from __future__ import annotations

from typing import Any

from app.plugins.base_notification import BaseNotification


class ExampleConsoleNotifier(BaseNotification):
    """Example notification plugin."""

    channel_name = "example_console"

    def send(self, message: str, *, context: dict[str, Any] | None = None) -> bool:
        return True
