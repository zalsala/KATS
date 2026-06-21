"""WebSocket subscription DTO."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.broker.kis.websocket.ws_tr_ids import (
    TR_TYPE_SUBSCRIBE,
    TR_TYPE_UNSUBSCRIBE,
    WS_TR_EXECUTION_NOTICE_MOCK,
    WS_TR_EXECUTION_NOTICE_REAL,
    WS_TR_REALTIME_ORDERBOOK,
    WS_TR_REALTIME_PRICE,
)

SubscriptionAction = Literal["subscribe", "unsubscribe"]


class SubscribeRequest(BaseModel):
    """WebSocket subscription request."""

    tr_id: str
    tr_key: str
    action: SubscriptionAction = "subscribe"

    @classmethod
    def for_price(
        cls, symbol_code: str, *, action: SubscriptionAction = "subscribe"
    ) -> SubscribeRequest:
        """Create a realtime price subscription."""
        return cls(tr_id=WS_TR_REALTIME_PRICE, tr_key=symbol_code, action=action)

    @classmethod
    def for_orderbook(
        cls,
        symbol_code: str,
        *,
        action: SubscriptionAction = "subscribe",
    ) -> SubscribeRequest:
        """Create a realtime orderbook subscription."""
        return cls(tr_id=WS_TR_REALTIME_ORDERBOOK, tr_key=symbol_code, action=action)

    @classmethod
    def for_execution_notice(
        cls,
        hts_id: str,
        *,
        is_mock: bool = True,
        action: SubscriptionAction = "subscribe",
    ) -> SubscribeRequest:
        """Create an execution notice subscription."""
        tr_id = WS_TR_EXECUTION_NOTICE_MOCK if is_mock else WS_TR_EXECUTION_NOTICE_REAL
        return cls(tr_id=tr_id, tr_key=hts_id, action=action)

    @property
    def tr_type(self) -> str:
        """Return KIS tr_type header value."""
        return TR_TYPE_SUBSCRIBE if self.action == "subscribe" else TR_TYPE_UNSUBSCRIBE

    @property
    def subscription_key(self) -> str:
        """Return a stable key for deduplication."""
        return f"{self.tr_id}:{self.tr_key}"
