"""Indicator display metadata for chart overlays and legend."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.indicator.indicator_series import IndicatorSeriesMap

INDICATOR_COLOR_HEX: dict[str, str] = {
    "SMA": "#42a5f5",
    "EMA": "#ab47bc",
    "VWAP": "#ffa726",
}

_SMA_PATTERN = re.compile(r"^SMA(\d+)$")
_EMA_PATTERN = re.compile(r"^EMA(\d+)$")


def indicator_color_hex(name: str) -> str:
    """Return the hex color used for an indicator series name."""
    if name.startswith("SMA"):
        return INDICATOR_COLOR_HEX["SMA"]
    if name.startswith("EMA"):
        return INDICATOR_COLOR_HEX["EMA"]
    return INDICATOR_COLOR_HEX.get(name, "#e0e0e0")


def format_indicator_label(name: str) -> str:
    """Return a human-readable legend label such as ``SMA(20)``."""
    sma_match = _SMA_PATTERN.match(name)
    if sma_match:
        return f"SMA({sma_match.group(1)})"
    ema_match = _EMA_PATTERN.match(name)
    if ema_match:
        return f"EMA({ema_match.group(1)})"
    return name


def format_indicator_value(value: Decimal) -> str:
    """Format an indicator value with chart price precision."""
    return f"{value:.0f}"


def format_indicator_inspection_value(value: Decimal) -> str:
    """Format an indicator value for hover inspection tooltips."""
    return f"{value:.1f}"


def indicator_series_sort_key(name: str) -> tuple[int, str]:
    """Return a stable sort key for indicator overlay names."""
    if name.startswith("SMA"):
        return (0, name)
    if name.startswith("EMA"):
        return (1, name)
    if name == "VWAP":
        return (2, name)
    return (3, name)


def _legend_sort_key(name: str) -> tuple[int, str]:
    return indicator_series_sort_key(name)


@dataclass(frozen=True, slots=True)
class IndicatorLegendItem:
    """Display metadata for one active indicator legend row."""

    series_name: str
    label: str
    color_hex: str
    latest_value: Decimal
    formatted_value: str


def build_legend_items(series: IndicatorSeriesMap) -> tuple[IndicatorLegendItem, ...]:
    """Build legend rows from existing indicator overlay series."""
    items: list[IndicatorLegendItem] = []
    for name in sorted(series.keys(), key=_legend_sort_key):
        points = series[name]
        if not points:
            continue
        latest_value = points[-1][1]
        items.append(
            IndicatorLegendItem(
                series_name=name,
                label=format_indicator_label(name),
                color_hex=indicator_color_hex(name),
                latest_value=latest_value,
                formatted_value=format_indicator_value(latest_value),
            )
        )
    return tuple(items)
