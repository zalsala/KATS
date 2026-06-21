"""Base view model."""

from __future__ import annotations

from collections.abc import Callable


class ViewModelBase:
    """Observable view model base class."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[str], None]] = []

    def add_listener(self, callback: Callable[[str], None]) -> None:
        """Register a change listener."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]) -> None:
        """Remove a change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self, field: str = "") -> None:
        """Notify listeners of a state change."""
        for listener in list(self._listeners):
            listener(field)
