"""Chart hover tooltip overlay widget."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from app.ui.chart.candle_inspector import CandleInspection, candle_center_x

TOOLTIP_BACKGROUND = QColor(30, 30, 30, 220)
TOOLTIP_BORDER = QColor("#616161")
TOOLTIP_TEXT_COLOR = QColor("#e0e0e0")
TOOLTIP_PADDING = 8
TOOLTIP_LINE_HEIGHT = 16
TOOLTIP_OFFSET_X = 12
TOOLTIP_OFFSET_Y = 12


class ChartHoverTooltip(QWidget):
    """OHLCV and indicator inspection tooltip for hovered candles."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._inspection: CandleInspection | None = None
        self._anchor = QPoint()
        self._plot_rect = QRect()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)

    @property
    def inspection(self) -> CandleInspection | None:
        """Return the tooltip inspection payload."""
        return self._inspection

    def set_inspection(
        self,
        inspection: CandleInspection | None,
        *,
        anchor: QPoint,
        plot_area: QRect,
        candle_index: int,
        candle_count: int,
    ) -> None:
        """Update tooltip content and position."""
        self._inspection = inspection
        self._anchor = anchor
        self._plot_rect = plot_area

        if inspection is None or candle_count <= 0:
            self.clear()
            return

        self._update_size(inspection)
        self.move(self._clamped_position(candle_index, candle_count))
        self.setVisible(True)
        self.update()

    def clear(self) -> None:
        """Hide the tooltip."""
        self._inspection = None
        self.setVisible(False)
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        if self._inspection is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(TOOLTIP_BORDER, 1))
        painter.setBrush(TOOLTIP_BACKGROUND)
        painter.drawRoundedRect(self.rect(), 4, 4)

        y = TOOLTIP_PADDING
        painter.setPen(TOOLTIP_TEXT_COLOR)
        painter.drawText(
            TOOLTIP_PADDING,
            y,
            self.width() - TOOLTIP_PADDING * 2,
            TOOLTIP_LINE_HEIGHT,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._inspection.timestamp_line,
        )
        y += TOOLTIP_LINE_HEIGHT

        for line in self._inspection.ohlc_lines:
            painter.drawText(
                TOOLTIP_PADDING,
                y,
                self.width() - TOOLTIP_PADDING * 2,
                TOOLTIP_LINE_HEIGHT,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                line,
            )
            y += TOOLTIP_LINE_HEIGHT

        for indicator_line in self._inspection.indicator_lines:
            painter.setPen(QColor(indicator_line.color_hex))
            painter.drawText(
                TOOLTIP_PADDING,
                y,
                self.width() - TOOLTIP_PADDING * 2,
                TOOLTIP_LINE_HEIGHT,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{indicator_line.label}: {indicator_line.formatted_value}",
            )
            y += TOOLTIP_LINE_HEIGHT

        painter.end()

    def _update_size(self, inspection: CandleInspection) -> None:
        font_metrics = self.fontMetrics()
        lines = [
            inspection.timestamp_line,
            *inspection.ohlc_lines,
            *(f"{line.label}: {line.formatted_value}" for line in inspection.indicator_lines),
        ]
        max_width = max(font_metrics.horizontalAdvance(line) for line in lines)
        line_count = len(lines)
        width = TOOLTIP_PADDING * 2 + max_width
        height = TOOLTIP_PADDING * 2 + line_count * TOOLTIP_LINE_HEIGHT
        self.setFixedSize(width, height)

    def _clamped_position(self, candle_index: int, candle_count: int) -> QPoint:
        center_x = candle_center_x(candle_index, self._plot_rect, candle_count)
        preferred_x = center_x + TOOLTIP_OFFSET_X
        preferred_y = self._anchor.y() + TOOLTIP_OFFSET_Y

        max_x = self._plot_rect.right() - self.width()
        max_y = self._plot_rect.bottom() - self.height()
        clamped_x = max(self._plot_rect.left(), min(preferred_x, max_x))
        clamped_y = max(self._plot_rect.top(), min(preferred_y, max_y))
        return QPoint(clamped_x, clamped_y)
