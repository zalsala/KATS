"""View binding helpers."""

from __future__ import annotations

from collections.abc import Callable

from app.ui.viewmodels.base import ViewModelBase


def bind_view_model(view_model: ViewModelBase, callback: Callable[[str], None]) -> None:
    """Register a view refresh callback on a view model."""
    view_model.add_listener(callback)
