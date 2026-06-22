"""Chart crosshair overlay widget."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from app.ui.chart.candle_inspector import HoverState
from app.ui.chart.chart_layout import plot_rect

CROSSHAIR_COLOR = QColor("#bdbdbd")


class ChartCrosshair(QWidget):
    """Mouse-following crosshair overlay for the chart plot area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hover = HoverState()
        self._plot_rect = plot_rect(self.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)

    @property
    def hover_state(self) -> HoverState:
        """Return the current crosshair hover state."""
        return self._hover

    def set_hover(self, hover: HoverState, plot_area: QRect) -> None:
        """Update crosshair position and visibility."""
        self._hover = hover
        self._plot_rect = plot_area
        self.setVisible(hover.active)
        self.update()

    def clear(self) -> None:
        """Hide the crosshair."""
        self._hover = HoverState()
        self.setVisible(False)
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        if not self._hover.active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(CROSSHAIR_COLOR, 1, Qt.PenStyle.DashLine))

        x = self._hover.cursor_x
        y = self._hover.cursor_y
        painter.drawLine(x, self._plot_rect.top(), x, self._plot_rect.bottom())
        painter.drawLine(self._plot_rect.left(), y, self._plot_rect.right(), y)
        painter.end()
