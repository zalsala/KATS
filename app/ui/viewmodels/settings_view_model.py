"""Settings view model."""

from __future__ import annotations

from app.ui.viewmodels.base import ViewModelBase


class SettingsViewModel(ViewModelBase):
    """State for the settings view."""

    def __init__(self) -> None:
        super().__init__()
        self.environment: str = ""
        self.account_type: str = ""
        self.application_version: str = ""

    def update(
        self,
        *,
        environment: str,
        account_type: str,
        application_version: str,
    ) -> None:
        self.environment = environment
        self.account_type = account_type
        self.application_version = application_version
        self.notify("settings")
