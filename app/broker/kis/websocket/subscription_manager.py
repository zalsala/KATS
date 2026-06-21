"""WebSocket subscription manager."""

from __future__ import annotations

import json

from app.dto.websocket.subscribe_request import SubscribeRequest


class SubscriptionManager:
    """Tracks active subscriptions and builds KIS subscribe payloads."""

    def __init__(self) -> None:
        self._active: dict[str, SubscribeRequest] = {}

    def register(self, request: SubscribeRequest) -> None:
        """Register or remove a subscription based on action."""
        key = request.subscription_key
        if request.action == "subscribe":
            self._active[key] = request.model_copy(update={"action": "subscribe"})
        elif key in self._active:
            del self._active[key]

    def all_subscriptions(self) -> tuple[SubscribeRequest, ...]:
        """Return all active subscribe requests for resubscribe."""
        return tuple(self._active.values())

    def build_payload(self, approval_key: str, request: SubscribeRequest) -> str:
        """Build a KIS WebSocket subscribe/unsubscribe JSON payload."""
        message = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": request.tr_type,
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": request.tr_id,
                    "tr_key": request.tr_key,
                }
            },
        }
        return json.dumps(message, ensure_ascii=False)

    def clear(self) -> None:
        """Remove all tracked subscriptions."""
        self._active.clear()
