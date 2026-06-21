"""KIS WebSocket message parser."""

from __future__ import annotations

import json
from typing import Any

from app.broker.kis.websocket.exceptions import WebSocketParseError
from app.broker.kis.websocket.ws_tr_ids import (
    WS_TR_EXECUTION_NOTICE_MOCK,
    WS_TR_EXECUTION_NOTICE_REAL,
    WS_TR_REALTIME_ORDERBOOK,
    WS_TR_REALTIME_PRICE,
)
from app.dto.websocket.ws_messages import (
    ExecutionNoticeMessage,
    RealtimeOrderbookMessage,
    RealtimePriceMessage,
)

ParsedWsMessage = RealtimePriceMessage | RealtimeOrderbookMessage | ExecutionNoticeMessage


class MessageParser:
    """Parses raw KIS WebSocket frames into DTOs."""

    def parse(self, raw: str) -> ParsedWsMessage | None:
        """Parse a raw WebSocket message.

        Args:
            raw: Raw text frame from KIS WebSocket.

        Returns:
            Parsed DTO, or None for heartbeat/system frames.
        """
        stripped = raw.strip()
        if not stripped:
            return None
        if stripped.startswith("{"):
            return self._parse_json(stripped)
        if "|" in stripped:
            return self._parse_pipe(stripped)
        if stripped in {"PINGPONG", "PING", "PONG"}:
            return None
        msg = f"Unsupported WebSocket message format: {stripped[:40]}"
        raise WebSocketParseError(msg)

    def _parse_json(self, raw: str) -> ParsedWsMessage | None:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None
        body = payload.get("body")
        if isinstance(body, dict):
            output = body.get("output")
            if isinstance(output, dict):
                return self._parse_output_dict(output)
        return None

    def _parse_pipe(self, raw: str) -> ParsedWsMessage | None:
        parts = raw.split("|")
        if len(parts) < 4:
            return None
        encrypt_flag, tr_id, _, data = parts[0], parts[1], parts[2], parts[3]
        if encrypt_flag not in {"0", "1"}:
            return None
        fields = data.split("^")
        if tr_id == WS_TR_REALTIME_PRICE:
            return self._parse_price(tr_id, fields)
        if tr_id == WS_TR_REALTIME_ORDERBOOK:
            return self._parse_orderbook(tr_id, fields)
        if tr_id in {WS_TR_EXECUTION_NOTICE_MOCK, WS_TR_EXECUTION_NOTICE_REAL}:
            return self._parse_execution(tr_id, fields)
        return None

    @staticmethod
    def _parse_output_dict(output: dict[str, Any]) -> ParsedWsMessage | None:
        tr_id = str(output.get("tr_id", ""))
        if tr_id == WS_TR_REALTIME_PRICE:
            return RealtimePriceMessage(
                symbol_code=str(output.get("mksc_shrn_iscd", "")),
                price=str(output.get("stck_prpr", "")),
                trade_time=str(output.get("stck_cntg_hour", "")),
                raw_tr_id=tr_id,
            )
        return None

    @staticmethod
    def _parse_price(tr_id: str, fields: list[str]) -> RealtimePriceMessage | None:
        if len(fields) < 3:
            return None
        return RealtimePriceMessage(
            symbol_code=fields[0],
            trade_time=fields[1],
            price=fields[2],
            change_sign=fields[3] if len(fields) > 3 else "",
            change_amount=fields[4] if len(fields) > 4 else "",
            volume=fields[5] if len(fields) > 5 else "",
            raw_tr_id=tr_id,
        )

    @staticmethod
    def _parse_orderbook(tr_id: str, fields: list[str]) -> RealtimeOrderbookMessage | None:
        if len(fields) < 5:
            return None
        return RealtimeOrderbookMessage(
            symbol_code=fields[0],
            ask_price_1=fields[1],
            ask_volume_1=fields[2],
            bid_price_1=fields[3],
            bid_volume_1=fields[4],
            raw_tr_id=tr_id,
        )

    @staticmethod
    def _parse_execution(tr_id: str, fields: list[str]) -> ExecutionNoticeMessage | None:
        if len(fields) < 6:
            return None
        return ExecutionNoticeMessage(
            account_no=fields[0],
            order_number=fields[1],
            symbol_code=fields[2],
            side=fields[3],
            executed_quantity=fields[4],
            executed_price=fields[5],
            raw_tr_id=tr_id,
        )
