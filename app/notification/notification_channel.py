"""Notification delivery channel definitions."""

from __future__ import annotations

from enum import StrEnum


class NotificationChannel(StrEnum):
    """Supported notification delivery channels."""

    CONSOLE = "console"
    UI = "ui"
    PLUGIN = "plugin"
