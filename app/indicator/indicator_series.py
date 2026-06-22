"""Indicator overlay series helpers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.chart.candle import Candle
from app.indicator.indicator import Indicator

IndicatorPoint = tuple[datetime, Decimal]
IndicatorSeriesMap = dict[str, list[IndicatorPoint]]


def build_series_from_candles(
    candles: list[Candle],
    indicator: Indicator,
) -> list[IndicatorPoint]:
    """Replay candles through an indicator and collect overlay points."""
    series: list[IndicatorPoint] = []
    for candle in candles:
        indicator.update(candle)
        value = indicator.value()
        if value is not None:
            series.append((candle.timestamp, value))
    return series
