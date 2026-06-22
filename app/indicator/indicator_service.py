"""Indicator registry and routing service."""

from __future__ import annotations

from decimal import Decimal

from app.chart.candle import Candle
from app.indicator.indicator import Indicator

SeriesKey = tuple[str, str]


class IndicatorService:
    """Maintain indicators per symbol and timeframe."""

    def __init__(self) -> None:
        self._indicators: dict[SeriesKey, dict[str, Indicator]] = {}

    def register_indicator(
        self,
        symbol: str,
        timeframe: str,
        name: str,
        indicator: Indicator,
    ) -> None:
        """Register an indicator for a symbol and timeframe series."""
        key = (symbol, timeframe)
        series = self._indicators.setdefault(key, {})
        series[name] = indicator

    def update_candle(self, candle: Candle) -> None:
        """Update all indicators registered for the candle series."""
        key = (candle.symbol, candle.interval)
        for indicator in self._indicators.get(key, {}).values():
            indicator.update(candle)

    def get_indicator_value(
        self,
        symbol: str,
        timeframe: str,
        name: str,
    ) -> Decimal | None:
        """Return the latest value for a registered indicator."""
        indicator = self._indicators.get((symbol, timeframe), {}).get(name)
        if indicator is None:
            return None
        return indicator.value()

    def list_indicator_names(self, symbol: str, timeframe: str) -> tuple[str, ...]:
        """Return registered indicator names for a series."""
        return tuple(self._indicators.get((symbol, timeframe), {}).keys())


def build_indicator_service() -> IndicatorService:
    """Create an IndicatorService with no pre-registered indicators."""
    return IndicatorService()
