"""KIS WebSocket client implementation."""

from __future__ import annotations

import logging

from app.broker.kis.auth.approval_key_manager import ApprovalKeyManager
from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.websocket.exceptions import WebSocketConnectionError
from app.broker.kis.websocket.message_parser import MessageParser, ParsedWsMessage
from app.broker.kis.websocket.reconnect_manager import ReconnectManager
from app.broker.kis.websocket.subscription_manager import SubscriptionManager
from app.broker.kis.websocket.ws_transport import WsTransport
from app.core.constants import DEFAULT_WS_TIMEOUT
from app.dto.websocket.subscribe_request import SubscribeRequest

logger = logging.getLogger(__name__)


class KisWebSocketClient:
    """KIS WebSocket client using ApprovalKeyManager and injectable transport."""

    def __init__(
        self,
        *,
        websocket_url: str,
        transport: WsTransport,
        approval_key_manager: ApprovalKeyManager,
        header_builder: HeaderBuilder,
        subscription_manager: SubscriptionManager | None = None,
        message_parser: MessageParser | None = None,
        reconnect_manager: ReconnectManager | None = None,
        receive_timeout: float = DEFAULT_WS_TIMEOUT,
    ) -> None:
        self._websocket_url = websocket_url
        self._transport = transport
        self._approval_key_manager = approval_key_manager
        self._header_builder = header_builder
        self._subscriptions = subscription_manager or SubscriptionManager()
        self._parser = message_parser or MessageParser()
        self._reconnect = reconnect_manager or ReconnectManager()
        self._receive_timeout = receive_timeout

    @property
    def is_connected(self) -> bool:
        return self._transport.is_open

    @property
    def subscription_manager(self) -> SubscriptionManager:
        return self._subscriptions

    def connect(self) -> None:
        """Connect using approval key from ApprovalKeyManager."""
        approval = self._approval_key_manager.get_approval_key()
        headers = self._header_builder.build_ws_headers(approval.key)
        logger.info("Connecting WebSocket url=%s", self._websocket_url)
        try:
            self._transport.connect(self._websocket_url, headers)
        except Exception as exc:
            msg = f"WebSocket connection failed: {exc}"
            raise WebSocketConnectionError(msg) from exc
        self._reconnect.reset()
        logger.info("WebSocket connected")

    def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._transport.close()
        logger.info("WebSocket disconnected")

    def subscribe(self, request: SubscribeRequest) -> None:
        """Subscribe to a realtime channel."""
        self._ensure_connected()
        approval = self._approval_key_manager.get_approval_key()
        payload = self._subscriptions.build_payload(approval.key, request)
        self._transport.send(payload)
        self._subscriptions.register(request)
        logger.info("Subscribed tr_id=%s tr_key=%s", request.tr_id, request.tr_key)

    def unsubscribe(self, request: SubscribeRequest) -> None:
        """Unsubscribe from a realtime channel."""
        self._ensure_connected()
        unsub = request.model_copy(update={"action": "unsubscribe"})
        approval = self._approval_key_manager.get_approval_key()
        payload = self._subscriptions.build_payload(approval.key, unsub)
        self._transport.send(payload)
        self._subscriptions.register(unsub)
        logger.info("Unsubscribed tr_id=%s tr_key=%s", request.tr_id, request.tr_key)

    def receive(self, timeout: float | None = None) -> ParsedWsMessage | None:
        """Receive and parse the next realtime message."""
        self._ensure_connected()
        raw = self._transport.receive(timeout or self._receive_timeout)
        if raw is None:
            return None
        return self._parser.parse(raw)

    def reconnect(self) -> None:
        """Reconnect with backoff and restore all subscriptions."""
        if not self._reconnect.should_retry():
            msg = "WebSocket reconnect attempts exhausted"
            raise WebSocketConnectionError(msg)

        self._reconnect.record_attempt()
        delay = self._reconnect.wait_before_retry()
        logger.warning("WebSocket reconnect attempt=%s delay=%ss", self._reconnect.attempts, delay)

        if self._transport.is_open:
            self._transport.close()

        self.connect()
        for subscription in self._subscriptions.all_subscriptions():
            self.subscribe(subscription)
        logger.info("WebSocket resubscribed count=%s", len(self._subscriptions.all_subscriptions()))

    def _ensure_connected(self) -> None:
        if not self._transport.is_open:
            msg = "WebSocket is not connected"
            raise WebSocketConnectionError(msg)
