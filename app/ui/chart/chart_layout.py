"""Shared chart layout constants and geometry helpers."""

from __future__ import annotations

from PySide6.QtCore import QRect

MARGIN_LEFT = 56
MARGIN_RIGHT = 12
MARGIN_TOP = 12
MARGIN_BOTTOM = 28


def plot_rect(widget_rect: QRect) -> QRect:
    """Return the inner candle plot area inside chart margins."""
    return widget_rect.adjusted(
        MARGIN_LEFT,
        MARGIN_TOP,
        -MARGIN_RIGHT,
        -MARGIN_BOTTOM,
    )
