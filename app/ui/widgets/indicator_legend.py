"""Indicator legend overlay widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from app.indicator.indicator_display import IndicatorLegendItem

LEGEND_BACKGROUND = QColor(30, 30, 30, 200)
LEGEND_TEXT_COLOR = QColor("#e0e0e0")
LEGEND_PADDING = 6
LEGEND_ROW_HEIGHT = 18
LEGEND_MARKER_WIDTH = 14
LEGEND_MARKER_GAP = 6


class IndicatorLegend(QWidget):
    """Compact legend overlay for active chart indicators."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: tuple[IndicatorLegendItem, ...] = ()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)

    @property
    def items(self) -> tuple[IndicatorLegendItem, ...]:
        """Return the currently displayed legend rows."""
        return self._items

    def set_items(self, items: tuple[IndicatorLegendItem, ...]) -> None:
        """Replace legend rows and hide when no indicators are active."""
        self._items = items
        self.setVisible(bool(items))
        self._update_size()
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        if not self._items:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), LEGEND_BACKGROUND)

        y = LEGEND_PADDING
        for item in self._items:
            color = QColor(item.color_hex)
            marker_y = y + LEGEND_ROW_HEIGHT // 2
            painter.setPen(QPen(color, 2))
            painter.drawLine(
                LEGEND_PADDING,
                marker_y,
                LEGEND_PADDING + LEGEND_MARKER_WIDTH,
                marker_y,
            )

            painter.setPen(LEGEND_TEXT_COLOR)
            text_x = LEGEND_PADDING + LEGEND_MARKER_WIDTH + LEGEND_MARKER_GAP
            painter.drawText(
                text_x,
                y,
                self.width() - text_x - LEGEND_PADDING,
                LEGEND_ROW_HEIGHT,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"{item.label}  {item.formatted_value}",
            )
            y += LEGEND_ROW_HEIGHT

        painter.end()

    def _update_size(self) -> None:
        if not self._items:
            return

        font_metrics = self.fontMetrics()
        max_text_width = 0
        for item in self._items:
            text = f"{item.label}  {item.formatted_value}"
            text_width = font_metrics.horizontalAdvance(text)
            max_text_width = max(
                max_text_width,
                LEGEND_MARKER_WIDTH + LEGEND_MARKER_GAP + text_width,
            )

        width = LEGEND_PADDING * 2 + max_text_width
        height = LEGEND_PADDING * 2 + len(self._items) * LEGEND_ROW_HEIGHT
        self.setFixedSize(width, height)
