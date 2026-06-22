"""Candle chart widget."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QResizeEvent
from PySide6.QtWidgets import QWidget

from app.chart.candle import Candle
from app.indicator.indicator_display import build_legend_items, indicator_color_hex
from app.indicator.indicator_series import IndicatorSeriesMap
from app.ui.chart.candle_inspector import CandleInspector, HoverState
from app.ui.chart.chart_layout import plot_rect
from app.ui.widgets.chart_crosshair import ChartCrosshair
from app.ui.widgets.chart_hover_tooltip import ChartHoverTooltip
from app.ui.widgets.indicator_legend import IndicatorLegend

EMPTY_MESSAGE = "No chart data available"
BULL_COLOR = QColor("#26a69a")
BEAR_COLOR = QColor("#ef5350")
AXIS_COLOR = QColor("#9e9e9e")
BACKGROUND_COLOR = QColor("#1e1e1e")
TEXT_COLOR = QColor("#e0e0e0")
LEGEND_MARGIN = 8


def _indicator_color(name: str) -> QColor:
    """Resolve overlay color for dynamic indicator names such as SMA50."""
    return QColor(indicator_color_hex(name))


class ChartWidget(QWidget):
    """Simple QPainter-based candlestick chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candles: list[Candle] = []
        self._indicator_series: IndicatorSeriesMap = {}
        self._symbol = ""
        self._legend = IndicatorLegend(self)
        self._crosshair = ChartCrosshair(self)
        self._tooltip = ChartHoverTooltip(self)
        self._inspector = CandleInspector([], {})
        self._hover_state = HoverState()
        self._last_hover_pos: QPoint | None = None
        self.setMouseTracking(True)
        self.setMinimumHeight(240)

    @property
    def is_empty(self) -> bool:
        """Return True when no candle data is loaded."""
        return not self._candles

    @property
    def symbol(self) -> str:
        """Return the displayed symbol code."""
        return self._symbol

    @property
    def indicator_series(self) -> IndicatorSeriesMap:
        """Return the currently configured indicator overlay series."""
        return dict(self._indicator_series)

    @property
    def indicator_legend(self) -> IndicatorLegend:
        """Return the embedded indicator legend overlay."""
        return self._legend

    @property
    def crosshair(self) -> ChartCrosshair:
        """Return the embedded chart crosshair overlay."""
        return self._crosshair

    @property
    def hover_tooltip(self) -> ChartHoverTooltip:
        """Return the embedded hover tooltip overlay."""
        return self._tooltip

    @property
    def hover_state(self) -> HoverState:
        """Return the current chart hover state."""
        return self._hover_state

    def set_candles(self, candles: list[Candle], *, symbol: str = "") -> None:
        """Replace the displayed candle series."""
        self._candles = list(candles)
        self._symbol = symbol
        self._inspector = CandleInspector(self._candles, self._indicator_series)
        self._position_legend()
        self._refresh_hover()
        self.update()

    def set_indicator_series(self, series: IndicatorSeriesMap | None) -> None:
        """Replace overlay indicator line series."""
        self._indicator_series = dict(series or {})
        self._legend.set_items(build_legend_items(self._indicator_series))
        self._inspector = CandleInspector(self._candles, self._indicator_series)
        self._position_legend()
        self._refresh_hover()
        self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._crosshair.setGeometry(self.rect())
        self._position_legend()
        self._refresh_hover()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._update_hover_at(event.position().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self._clear_hover()
        super().leaveEvent(event)

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), BACKGROUND_COLOR)

        if not self._candles:
            painter.setPen(TEXT_COLOR)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, EMPTY_MESSAGE)
            painter.end()
            return

        chart_rect = plot_rect(self.rect())
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            painter.end()
            return

        min_price, max_price = _price_bounds(self._candles, self._indicator_series)
        self._draw_axes(painter, chart_rect, min_price, max_price)
        self._draw_candles(painter, chart_rect, min_price, max_price)
        self._draw_indicator_lines(painter, chart_rect, min_price, max_price)
        painter.end()

    def _draw_axes(
        self,
        painter: QPainter,
        chart_rect: QRect,
        min_price: Decimal,
        max_price: Decimal,
    ) -> None:
        painter.setPen(QPen(AXIS_COLOR, 1))
        painter.drawRect(chart_rect)

        painter.setPen(TEXT_COLOR)
        for index, _label in enumerate(_price_axis_labels(min_price, max_price)):
            y = chart_rect.top() + int(chart_rect.height() * index / 4)
            price = _price_for_axis_y(min_price, max_price, index / 4)
            painter.drawText(4, y + 4, f"{price:.0f}")
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

        time_labels = _time_axis_labels(self._candles)
        if time_labels:
            width = chart_rect.width()
            for position, label in time_labels:
                x = chart_rect.left() + int(width * position)
                painter.drawText(x - 16, chart_rect.bottom() + 18, label)

        if self._symbol:
            painter.drawText(chart_rect.left(), chart_rect.top() - 2, self._symbol)

    def _draw_candles(
        self,
        painter: QPainter,
        chart_rect: QRect,
        min_price: Decimal,
        max_price: Decimal,
    ) -> None:
        count = len(self._candles)
        if count == 0:
            return

        slot_width = chart_rect.width() / count
        body_width = max(4, int(slot_width * 0.6))

        for index, candle in enumerate(self._candles):
            center_x = chart_rect.left() + int((index + 0.5) * slot_width)
            high_y = _price_to_y(candle.high, min_price, max_price, chart_rect)
            low_y = _price_to_y(candle.low, min_price, max_price, chart_rect)
            open_y = _price_to_y(candle.open, min_price, max_price, chart_rect)
            close_y = _price_to_y(candle.close, min_price, max_price, chart_rect)

            color = BULL_COLOR if candle.close >= candle.open else BEAR_COLOR
            painter.setPen(QPen(color, 1))
            painter.drawLine(center_x, high_y, center_x, low_y)

            top = min(open_y, close_y)
            bottom = max(open_y, close_y)
            if bottom - top < 1:
                bottom = top + 1
            painter.fillRect(
                center_x - body_width // 2,
                top,
                body_width,
                bottom - top,
                color,
            )

    def _draw_indicator_lines(
        self,
        painter: QPainter,
        chart_rect: QRect,
        min_price: Decimal,
        max_price: Decimal,
    ) -> None:
        if not self._indicator_series:
            return

        count = len(self._candles)
        if count == 0:
            return

        slot_width = chart_rect.width() / count
        candle_index = {candle.timestamp: index for index, candle in enumerate(self._candles)}

        for name, points in self._indicator_series.items():
            if not points:
                continue

            color = _indicator_color(name)
            painter.setPen(QPen(color, 2))
            previous_point: tuple[int, int] | None = None

            for timestamp, value in points:
                index = candle_index.get(timestamp)
                if index is None:
                    continue
                x = chart_rect.left() + int((index + 0.5) * slot_width)
                y = _price_to_y(value, min_price, max_price, chart_rect)
                if previous_point is not None:
                    painter.drawLine(previous_point[0], previous_point[1], x, y)
                previous_point = (x, y)

    def _position_legend(self) -> None:
        if not self._legend.isVisible():
            return

        chart_rect = plot_rect(self.rect())
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        legend_x = chart_rect.right() - self._legend.width() - LEGEND_MARGIN
        legend_y = chart_rect.top() + LEGEND_MARGIN
        self._legend.move(legend_x, legend_y)
        self._legend.raise_()

    def _update_hover_at(self, position: QPoint) -> None:
        if not self._candles:
            self._clear_hover()
            return

        plot_area = plot_rect(self.rect())
        hover = self._inspector.resolve_hover(position, plot_area)
        if not hover.active:
            self._clear_hover()
            return

        self._last_hover_pos = position
        self._hover_state = hover
        self._crosshair.set_hover(hover, plot_area)
        inspection = hover.inspection
        if inspection is not None and hover.candle_index is not None:
            self._tooltip.set_inspection(
                inspection,
                anchor=position,
                plot_area=plot_area,
                candle_index=hover.candle_index,
                candle_count=len(self._candles),
            )
        else:
            self._tooltip.clear()
        self._crosshair.raise_()
        self._tooltip.raise_()

    def _refresh_hover(self) -> None:
        if self._last_hover_pos is None:
            return
        self._update_hover_at(self._last_hover_pos)

    def _clear_hover(self) -> None:
        self._last_hover_pos = None
        self._hover_state = HoverState()
        self._crosshair.clear()
        self._tooltip.clear()


def _price_bounds(
    candles: list[Candle],
    indicator_series: IndicatorSeriesMap,
) -> tuple[Decimal, Decimal]:
    min_price = min(candle.low for candle in candles)
    max_price = max(candle.high for candle in candles)

    for points in indicator_series.values():
        for _timestamp, value in points:
            min_price = min(min_price, value)
            max_price = max(max_price, value)

    if min_price == max_price:
        return min_price - Decimal("1"), max_price + Decimal("1")
    padding = (max_price - min_price) * Decimal("0.05")
    return min_price - padding, max_price + padding


def _price_for_axis_y(min_price: Decimal, max_price: Decimal, ratio: float) -> Decimal:
    span = max_price - min_price
    return max_price - (span * Decimal(str(ratio)))


def _price_to_y(
    price: Decimal,
    min_price: Decimal,
    max_price: Decimal,
    chart_rect: QRect,
) -> int:
    span = max_price - min_price
    if span == 0:
        return int(chart_rect.center().y())
    ratio = (max_price - price) / span
    return int(chart_rect.top() + chart_rect.height() * float(ratio))


def _price_axis_labels(min_price: Decimal, max_price: Decimal) -> list[str]:
    return [str(_price_for_axis_y(min_price, max_price, index / 4)) for index in range(5)]


def _time_axis_labels(candles: list[Candle]) -> list[tuple[float, str]]:
    if not candles:
        return []
    indices = {0, len(candles) // 2, len(candles) - 1}
    labels: list[tuple[float, str]] = []
    for index in sorted(indices):
        position = 0.0 if len(candles) == 1 else index / (len(candles) - 1)
        labels.append((position, candles[index].timestamp.strftime("%H:%M")))
    return labels
