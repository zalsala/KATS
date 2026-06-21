"""WebSocket application service — external entry point."""

from __future__ import annotations

from datetime import UTC, datetime

from app.broker.interfaces.ws_client import ParsedMessage, WebSocketClient
from app.core.logging import CorrelationContext
from app.domain.realtime.entities import ExecutionNotice, RealtimeOrderbook, RealtimePrice
from app.dto.websocket.subscribe_request import SubscribeRequest
from app.dto.websocket.ws_messages import (
    ExecutionNoticeMessage,
    RealtimeOrderbookMessage,
    RealtimePriceMessage,
)


class WebSocketService:
    """External entry point for realtime WebSocket features."""

    def __init__(self, *, ws_client: WebSocketClient) -> None:
        self._client = ws_client

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    def connect(self) -> None:
        """Open WebSocket connection."""
        self._client.connect()

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._client.disconnect()

    def subscribe_price(self, symbol_code: str) -> None:
        """Subscribe to realtime price for a symbol."""
        self._client.subscribe(SubscribeRequest.for_price(symbol_code))

    def subscribe_orderbook(self, symbol_code: str) -> None:
        """Subscribe to realtime orderbook for a symbol."""
        self._client.subscribe(SubscribeRequest.for_orderbook(symbol_code))

    def subscribe_execution_notice(self, hts_id: str, *, is_mock: bool = True) -> None:
        """Subscribe to execution notices for an HTS ID."""
        self._client.subscribe(SubscribeRequest.for_execution_notice(hts_id, is_mock=is_mock))

    def unsubscribe_price(self, symbol_code: str) -> None:
        """Unsubscribe from realtime price."""
        self._client.unsubscribe(SubscribeRequest.for_price(symbol_code, action="unsubscribe"))

    def receive(
        self,
        timeout: float | None = None,
    ) -> RealtimePrice | RealtimeOrderbook | ExecutionNotice | None:
        """Receive the next parsed realtime entity."""
        with CorrelationContext():
            message = self._client.receive(timeout=timeout)
        if message is None:
            return None
        return self._to_entity(message)

    def reconnect(self) -> None:
        """Reconnect and restore subscriptions."""
        self._client.reconnect()

    @staticmethod
    def _to_entity(
        message: ParsedMessage,
    ) -> RealtimePrice | RealtimeOrderbook | ExecutionNotice:
        received_at = datetime.now(UTC)
        if isinstance(message, RealtimePriceMessage):
            return RealtimePrice(
                symbol_code=message.symbol_code,
                price=message.price,
                trade_time=message.trade_time,
                received_at=received_at,
            )
        if isinstance(message, RealtimeOrderbookMessage):
            return RealtimeOrderbook(
                symbol_code=message.symbol_code,
                ask_price=message.ask_price_1,
                ask_volume=message.ask_volume_1,
                bid_price=message.bid_price_1,
                bid_volume=message.bid_volume_1,
                received_at=received_at,
            )
        if isinstance(message, ExecutionNoticeMessage):
            return ExecutionNotice(
                symbol_code=message.symbol_code,
                order_number=message.order_number,
                executed_quantity=message.executed_quantity,
                executed_price=message.executed_price,
                side=message.side,
                received_at=received_at,
            )
        msg = f"Unsupported message type: {type(message)}"
        raise TypeError(msg)


def build_websocket_service(*, ws_client: WebSocketClient) -> WebSocketService:
    """Create a WebSocketService wired with the given client."""
    return WebSocketService(ws_client=ws_client)
