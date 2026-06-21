"""PySide6 user interface."""

from app.ui.ui_session import UiSession
from app.ui.viewmodels import MainViewModel

__all__ = ["MainViewModel", "UiSession", "launch_ui"]


from pathlib import Path


def launch_ui(*, project_root: Path | None = None) -> int:
    """Lazy import to avoid heavy dependencies during test collection."""
    from app.ui.app_launcher import launch_ui as _launch_ui

    return _launch_ui(project_root=project_root)
