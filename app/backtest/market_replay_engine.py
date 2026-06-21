"""Market data replay engine."""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.backtest.historical_data_provider import HistoricalDataProvider
from app.domain.backtest.historical_bar import HistoricalBar
from app.events.domain_events import MarketDataEvent
from app.events.event_bus_service import EventBusService


class MarketReplayEngine:
    """Replays historical bars as MarketDataEvent sequentially."""

    def __init__(
        self,
        *,
        provider: HistoricalDataProvider,
        event_bus: EventBusService,
        source: str = "market_replay_engine",
    ) -> None:
        self._provider = provider
        self._event_bus = event_bus
        self._source = source
        self._logger = logging.getLogger(__name__)

    def replay(self, *, on_after_bar: Callable[[HistoricalBar], None] | None = None) -> int:
        """Publish all historical bars and return replay count."""
        count = 0
        for bar in self._provider.list_bars():
            self._event_bus.publish(
                MarketDataEvent(
                    source=self._source,
                    payload={
                        "symbol_code": bar.symbol_code,
                        "symbol": bar.symbol_code,
                        "price": str(bar.price),
                        "current_price": str(bar.price),
                        "timestamp": bar.timestamp.isoformat(),
                        "volume": str(bar.volume),
                    },
                    correlation_id=bar.timestamp.isoformat(),
                )
            )
            count += 1
            if on_after_bar is not None:
                on_after_bar(bar)
        self._logger.info("Replayed %s market data bars", count)
        return count
