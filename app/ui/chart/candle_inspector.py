"""Candle hover inspection logic for chart interaction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from PySide6.QtCore import QPoint, QRect

from app.chart.candle import Candle
from app.indicator.indicator_display import (
    format_indicator_inspection_value,
    format_indicator_label,
    indicator_color_hex,
    indicator_series_sort_key,
)
from app.indicator.indicator_series import IndicatorSeriesMap


@dataclass(frozen=True, slots=True)
class IndicatorInspectionLine:
    """Indicator value at a hovered candle."""

    label: str
    formatted_value: str
    color_hex: str


@dataclass(frozen=True, slots=True)
class CandleInspection:
    """OHLCV and indicator values for one hovered candle."""

    candle: Candle
    timestamp_line: str
    ohlc_lines: tuple[str, ...]
    indicator_lines: tuple[IndicatorInspectionLine, ...]


@dataclass(slots=True)
class HoverState:
    """Current chart hover interaction state."""

    active: bool = False
    cursor_x: int = 0
    cursor_y: int = 0
    candle_index: int | None = None
    inspection: CandleInspection | None = None


def format_candle_timestamp(timestamp: datetime) -> str:
    """Format a candle timestamp for tooltip display."""
    return timestamp.strftime("%Y-%m-%d %H:%M")


def format_volume(volume: int) -> str:
    """Format candle volume with thousands separators."""
    return f"{volume:,}"


def format_price_value(value: Decimal) -> str:
    """Format OHLC prices for tooltip display."""
    return f"{value:.0f}"


def candle_index_at_x(x: int, plot_rect: QRect, candle_count: int) -> int | None:
    """Resolve the hovered candle index from an x coordinate."""
    if candle_count <= 0 or plot_rect.width() <= 0:
        return None
    if x < plot_rect.left() or x > plot_rect.right():
        return None

    relative_x = x - plot_rect.left()
    slot_width = plot_rect.width() / candle_count
    index = int(relative_x / slot_width)
    return max(0, min(candle_count - 1, index))


def candle_center_x(index: int, plot_rect: QRect, candle_count: int) -> int:
    """Return the x coordinate at the center of a candle slot."""
    slot_width = plot_rect.width() / candle_count
    return plot_rect.left() + int((index + 0.5) * slot_width)


def indicator_value_at_timestamp(
    points: list[tuple[datetime, Decimal]],
    timestamp: datetime,
) -> Decimal | None:
    """Return the indicator value aligned to a candle timestamp."""
    for point_timestamp, value in points:
        if point_timestamp == timestamp:
            return value
    return None


class CandleInspector:
    """Resolve hover position to candle and indicator inspection data."""

    def __init__(
        self,
        candles: list[Candle],
        indicator_series: IndicatorSeriesMap,
    ) -> None:
        self._candles = list(candles)
        self._indicator_series = dict(indicator_series)

    @property
    def candles(self) -> list[Candle]:
        """Return the candle series used for inspection."""
        return list(self._candles)

    @property
    def indicator_series(self) -> IndicatorSeriesMap:
        """Return the indicator overlay series used for inspection."""
        return dict(self._indicator_series)

    def resolve_hover(self, position: QPoint, plot_rect: QRect) -> HoverState:
        """Build hover state for a cursor position inside the plot area."""
        if not plot_rect.contains(position) or not self._candles:
            return HoverState()

        candle_index = candle_index_at_x(position.x(), plot_rect, len(self._candles))
        if candle_index is None:
            return HoverState()

        inspection = self.inspect_candle(candle_index)
        return HoverState(
            active=True,
            cursor_x=position.x(),
            cursor_y=position.y(),
            candle_index=candle_index,
            inspection=inspection,
        )

    def inspect_candle(self, candle_index: int) -> CandleInspection | None:
        """Build inspection data for a candle index."""
        if candle_index < 0 or candle_index >= len(self._candles):
            return None

        candle = self._candles[candle_index]
        return CandleInspection(
            candle=candle,
            timestamp_line=format_candle_timestamp(candle.timestamp),
            ohlc_lines=self._build_ohlc_lines(candle),
            indicator_lines=self._build_indicator_lines(candle),
        )

    def _build_ohlc_lines(self, candle: Candle) -> tuple[str, ...]:
        return (
            f"O: {format_price_value(candle.open)}",
            f"H: {format_price_value(candle.high)}",
            f"L: {format_price_value(candle.low)}",
            f"C: {format_price_value(candle.close)}",
            f"V: {format_volume(candle.volume)}",
        )

    def _build_indicator_lines(self, candle: Candle) -> tuple[IndicatorInspectionLine, ...]:
        lines: list[IndicatorInspectionLine] = []
        for name in sorted(self._indicator_series, key=indicator_series_sort_key):
            points = self._indicator_series[name]
            value = indicator_value_at_timestamp(points, candle.timestamp)
            if value is None:
                continue
            lines.append(
                IndicatorInspectionLine(
                    label=format_indicator_label(name),
                    formatted_value=format_indicator_inspection_value(value),
                    color_hex=indicator_color_hex(name),
                )
            )
        return tuple(lines)
