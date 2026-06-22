"""Indicator registry and routing service."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from app.chart.candle import Candle
from app.indicator.ema_indicator import EmaIndicator
from app.indicator.indicator import Indicator
from app.indicator.indicator_series import IndicatorSeriesMap, build_series_from_candles
from app.indicator.sma_indicator import SmaIndicator
from app.indicator.vwap_indicator import VwapIndicator

SeriesKey = tuple[str, str]

DEFAULT_SMA_NAME = "SMA20"
DEFAULT_EMA_NAME = "EMA20"
DEFAULT_VWAP_NAME = "VWAP"

DEFAULT_OVERLAY_FACTORIES: dict[str, Callable[[], Indicator]] = {
    DEFAULT_SMA_NAME: lambda: SmaIndicator(20),
    DEFAULT_EMA_NAME: lambda: EmaIndicator(20),
    DEFAULT_VWAP_NAME: lambda: VwapIndicator(),
}


class IndicatorService:
    """Maintain indicators per symbol and timeframe."""

    def __init__(self) -> None:
        self._indicators: dict[SeriesKey, dict[str, Indicator]] = {}
        self._factories: dict[SeriesKey, dict[str, Callable[[], Indicator]]] = {}

    def register_indicator(
        self,
        symbol: str,
        timeframe: str,
        name: str,
        indicator: Indicator,
        *,
        factory: Callable[[], Indicator] | None = None,
    ) -> None:
        """Register an indicator for a symbol and timeframe series."""
        key = (symbol, timeframe)
        series = self._indicators.setdefault(key, {})
        series[name] = indicator
        if factory is not None:
            factories = self._factories.setdefault(key, {})
            factories[name] = factory

    def ensure_default_indicators(self, symbol: str, timeframe: str) -> None:
        """Register default overlay indicators for a series when missing."""
        for name, factory in DEFAULT_OVERLAY_FACTORIES.items():
            key = (symbol, timeframe)
            if name in self._indicators.get(key, {}):
                continue
            self.register_indicator(symbol, timeframe, name, factory(), factory=factory)

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

    def build_overlay_series(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Candle],
        *,
        names: tuple[str, ...] | None = None,
    ) -> IndicatorSeriesMap:
        """Build overlay point series by replaying candles through indicator factories."""
        key = (symbol, timeframe)
        selected_names = names or tuple(DEFAULT_OVERLAY_FACTORIES)
        factories = self._factories.get(key, {})
        series_map: IndicatorSeriesMap = {}

        for name in selected_names:
            factory = factories.get(name)
            if factory is None:
                continue
            series_map[name] = build_series_from_candles(candles, factory())

        return series_map

    def list_indicator_names(self, symbol: str, timeframe: str) -> tuple[str, ...]:
        """Return registered indicator names for a series."""
        return tuple(self._indicators.get((symbol, timeframe), {}).keys())


def build_indicator_service() -> IndicatorService:
    """Create an IndicatorService with no pre-registered indicators."""
    return IndicatorService()
