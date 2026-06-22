"""Build OHLCV candles from trade ticks."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.chart.candle import Candle

DEFAULT_INTERVAL = "1m"


def _to_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


def _minute_start(timestamp: datetime) -> datetime:
    """Align a timestamp to the start of its one-minute bucket."""
    return timestamp.replace(second=0, microsecond=0)


class CandleBuilder:
    """Aggregates trades into one-minute OHLCV candles."""

    def __init__(self, symbol: str, interval: str = DEFAULT_INTERVAL) -> None:
        self._symbol = symbol
        self._interval = interval
        self._current: Candle | None = None

    @property
    def symbol(self) -> str:
        return self._symbol

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
        """Apply a trade tick and return a finalized candle when the minute rolls over."""
        if volume < 0:
            msg = "Trade volume must be non-negative"
            raise ValueError(msg)

        trade_price = _to_decimal(price)
        bucket = _minute_start(timestamp)

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
