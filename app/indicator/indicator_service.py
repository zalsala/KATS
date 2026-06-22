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


def sma_indicator_name(period: int) -> str:
    """Return the overlay series name for an SMA period."""
    return f"SMA{period}"


def ema_indicator_name(period: int) -> str:
    """Return the overlay series name for an EMA period."""
    return f"EMA{period}"


def _make_sma_factory(period: int) -> Callable[[], Indicator]:
    def factory() -> Indicator:
        return SmaIndicator(period)

    return factory


def _make_ema_factory(period: int) -> Callable[[], Indicator]:
    def factory() -> Indicator:
        return EmaIndicator(period)

    return factory


def _make_vwap_factory() -> Callable[[], Indicator]:
    def factory() -> Indicator:
        return VwapIndicator()

    return factory


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
        self.configure_overlay_indicators(
            symbol,
            timeframe,
            sma_enabled=True,
            sma_period=20,
            ema_enabled=False,
            ema_period=20,
            vwap_enabled=False,
        )

    def configure_overlay_indicators(
        self,
        symbol: str,
        timeframe: str,
        *,
        sma_enabled: bool,
        sma_period: int,
        ema_enabled: bool,
        ema_period: int,
        vwap_enabled: bool,
    ) -> tuple[str, ...]:
        """Rebuild overlay indicators for a series and return enabled names."""
        self._clear_overlay_indicators(symbol, timeframe)
        enabled_names: list[str] = []

        if sma_enabled:
            name = sma_indicator_name(sma_period)
            factory = _make_sma_factory(sma_period)
            self.register_indicator(symbol, timeframe, name, factory(), factory=factory)
            enabled_names.append(name)

        if ema_enabled:
            name = ema_indicator_name(ema_period)
            factory = _make_ema_factory(ema_period)
            self.register_indicator(symbol, timeframe, name, factory(), factory=factory)
            enabled_names.append(name)

        if vwap_enabled:
            factory = _make_vwap_factory()
            self.register_indicator(
                symbol,
                timeframe,
                DEFAULT_VWAP_NAME,
                factory(),
                factory=factory,
            )
            enabled_names.append(DEFAULT_VWAP_NAME)

        return tuple(enabled_names)

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
        registered_names = tuple(self._factories.get(key, {}))
        selected_names = names or registered_names
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

    def _clear_overlay_indicators(self, symbol: str, timeframe: str) -> None:
        key = (symbol, timeframe)
        indicators = self._indicators.get(key)
        if indicators is None:
            return

        overlay_names = [
            name
            for name in indicators
            if name.startswith("SMA") or name.startswith("EMA") or name == DEFAULT_VWAP_NAME
        ]
        for name in overlay_names:
            del indicators[name]
            self._factories.get(key, {}).pop(name, None)


def build_indicator_service() -> IndicatorService:
    """Create an IndicatorService with no pre-registered indicators."""
    return IndicatorService()
