"""Publish WebSocket realtime entities as MarketDataEvent."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

from app.domain.realtime.entities import RealtimeOrderbook, RealtimePrice
from app.events.domain_events import MarketDataEvent

if TYPE_CHECKING:
    from app.events.event_bus_service import EventBusService
    from app.service.websocket.websocket_service import WebSocketService

logger = logging.getLogger(__name__)
SOURCE = "realtime_market_data_publisher"


class RealtimeMarketDataPublisher:
    """Background publisher that forwards WebSocket ticks to EventBus."""

    def __init__(
        self,
        *,
        websocket_service: WebSocketService,
        event_bus: EventBusService,
        receive_timeout: float = 1.0,
        poll_interval_seconds: float = 0.1,
    ) -> None:
        self._websocket_service = websocket_service
        self._event_bus = event_bus
        self._receive_timeout = receive_timeout
        self._poll_interval_seconds = poll_interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Return True when the publisher thread is alive."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the background publisher thread."""
        if not self._websocket_service.is_connected:
            logger.warning("RealtimeMarketDataPublisher start skipped: websocket not connected")
            return

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="realtime-market-data-publisher",
                daemon=True,
            )
            self._thread.start()
            logger.info("RealtimeMarketDataPublisher started")

    def stop(self) -> None:
        """Signal the publisher to stop and wait for the thread to exit."""
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                return
            self._stop_event.set()
            thread = self._thread

        thread.join(timeout=self._receive_timeout + self._poll_interval_seconds + 1.0)

        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None

        logger.info("RealtimeMarketDataPublisher stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                entity = self._websocket_service.receive(timeout=self._receive_timeout)
            except Exception:
                logger.exception("Realtime market data receive failed")
                self._stop_event.wait(self._poll_interval_seconds)
                continue

            if entity is None:
                self._stop_event.wait(self._poll_interval_seconds)
                continue

            try:
                self._publish_entity(entity)
            except Exception:
                logger.exception("Realtime market data publish failed")

    def _publish_entity(self, entity: RealtimePrice | RealtimeOrderbook | object) -> None:
        if isinstance(entity, RealtimePrice):
            self._event_bus.publish(
                MarketDataEvent(
                    source=SOURCE,
                    event_name="market_data.price.updated",
                    payload=_price_payload(entity),
                )
            )
            return

        if isinstance(entity, RealtimeOrderbook):
            self._event_bus.publish(
                MarketDataEvent(
                    source=SOURCE,
                    event_name="market_data.orderbook.updated",
                    payload=_orderbook_payload(entity),
                )
            )


def _price_payload(entity: RealtimePrice) -> dict[str, Any]:
    return {
        "symbol_code": entity.symbol_code,
        "symbol": entity.symbol_code,
        "price": entity.price,
        "current_price": entity.price,
        "trade_time": entity.trade_time,
        "received_at": entity.received_at.isoformat(),
        "volume": "1",
    }


def _orderbook_payload(entity: RealtimeOrderbook) -> dict[str, Any]:
    return {
        "symbol_code": entity.symbol_code,
        "symbol": entity.symbol_code,
        "price": entity.bid_price,
        "current_price": entity.bid_price,
        "bid_price": entity.bid_price,
        "ask_price": entity.ask_price,
        "bid_volume": entity.bid_volume,
        "ask_volume": entity.ask_volume,
        "received_at": entity.received_at.isoformat(),
        "volume": "1",
    }


def build_realtime_market_data_publisher(
    *,
    websocket_service: WebSocketService,
    event_bus: EventBusService,
    receive_timeout: float = 1.0,
    poll_interval_seconds: float = 0.1,
) -> RealtimeMarketDataPublisher:
    """Create a RealtimeMarketDataPublisher wired to WebSocket and EventBus."""
    return RealtimeMarketDataPublisher(
        websocket_service=websocket_service,
        event_bus=event_bus,
        receive_timeout=receive_timeout,
        poll_interval_seconds=poll_interval_seconds,
    )
