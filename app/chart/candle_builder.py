"""Build OHLCV candles from trade ticks."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.chart.candle import Candle
from app.chart.timeframe import DEFAULT_TIMEFRAME, Timeframe, resolve_timeframe

DEFAULT_INTERVAL = DEFAULT_TIMEFRAME.value


def _to_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


def bucket_start(timestamp: datetime, timeframe: Timeframe) -> datetime:
    """Align a timestamp to the start of its candle bucket."""
    aligned = timestamp.replace(second=0, microsecond=0)
    if timeframe == Timeframe.M1:
        return aligned
    if timeframe == Timeframe.M5:
        return aligned.replace(minute=(aligned.minute // 5) * 5)
    if timeframe == Timeframe.M15:
        return aligned.replace(minute=(aligned.minute // 15) * 15)
    if timeframe == Timeframe.H1:
        return aligned.replace(minute=0)
    msg = f"Unsupported timeframe: {timeframe}"
    raise ValueError(msg)


class CandleBuilder:
    """Aggregates trades into OHLCV candles for a single timeframe."""

    def __init__(
        self,
        symbol: str,
        *,
        timeframe: Timeframe | str = DEFAULT_TIMEFRAME,
        interval: str | None = None,
    ) -> None:
        self._symbol = symbol
        self._timeframe = resolve_timeframe(timeframe)
        self._interval = interval or self._timeframe.value
        self._current: Candle | None = None

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def timeframe(self) -> Timeframe:
        return self._timeframe

    @property
    def interval(self) -> str:
        return self._interval

    def update_trade(
        self,
        price: Decimal | str | int | float,
        volume: int,
        *,
        timestamp: datetime,
    ) -> Candle | None:
        """Apply a trade tick and return a finalized candle when the bucket rolls over."""
        if volume < 0:
            msg = "Trade volume must be non-negative"
            raise ValueError(msg)

        trade_price = _to_decimal(price)
        bucket = bucket_start(timestamp, self._timeframe)

        if self._current is None or self._current.timestamp != bucket:
            finalized = self.finalize()
            self._current = Candle(
                symbol=self._symbol,
                interval=self._interval,
                timestamp=bucket,
                open=trade_price,
                high=trade_price,
                low=trade_price,
                close=trade_price,
                volume=volume,
            )
            return finalized

        self._current.high = max(self._current.high, trade_price)
        self._current.low = min(self._current.low, trade_price)
        self._current.close = trade_price
        self._current.volume += volume
        return None

    def get_current_candle(self) -> Candle | None:
        """Return the in-progress candle, if any."""
        return self._current

    def finalize(self) -> Candle | None:
        """Finalize and clear the in-progress candle."""
        finalized = self._current
        self._current = None
        return finalized
