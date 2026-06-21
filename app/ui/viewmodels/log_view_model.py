"""Log view model."""

from __future__ import annotations

from app.ui.models.display_models import LogEntry
from app.ui.viewmodels.base import ViewModelBase


class LogViewModel(ViewModelBase):
    """State for the log view."""

    def __init__(self, *, max_entries: int = 500) -> None:
        super().__init__()
        self._max_entries = max_entries
        self.entries: list[LogEntry] = []

    def append(self, entry: LogEntry) -> None:
        self.entries.append(entry)
        if len(self.entries) > self._max_entries:
            self.entries = self.entries[-self._max_entries :]
        self.notify("log")

    def clear(self) -> None:
        self.entries.clear()
        self.notify("log")
