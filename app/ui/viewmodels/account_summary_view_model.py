"""Account summary view model."""

from __future__ import annotations

from app.domain.account.account_summary import AccountSummary
from app.domain.position.position_item import PositionItem
from app.ui.viewmodels.base import ViewModelBase


class AccountSummaryViewModel(ViewModelBase):
    """State for the embedded market account summary panel."""

    def __init__(self) -> None:
        super().__init__()
        self.summary: AccountSummary | None = None
        self.loading: bool = False
        self.lookup_enabled: bool = False
        self.lookup_status: str = ""
        self.error_message: str = ""

    def set_lookup_status(self, *, enabled: bool, message: str) -> None:
        """Update whether account summary lookup is currently allowed."""
        self.lookup_enabled = enabled
        self.lookup_status = message
        self.notify("lookup_status")

    def set_loading(self, loading: bool) -> None:
        self.loading = loading
        self.notify("loading")

    def set_summary(self, summary: AccountSummary | None) -> None:
        self.summary = summary
        self.notify("summary")

    def set_error_message(self, message: str) -> None:
        self.error_message = message
        self.notify("error_message")

    def clear_error_message(self) -> None:
        if not self.error_message:
            return
        self.error_message = ""
        self.notify("error_message")

    def recalculate_from_positions(self, positions: list[PositionItem]) -> None:
        """Update valuation metrics from refreshed holdings."""
        if self.summary is None:
            return
        self.summary = self.summary.with_positions(positions)
        self.notify("summary")
