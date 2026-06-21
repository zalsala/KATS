"""Realtime WebSocket message DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class RealtimePriceMessage(BaseModel):
    """Parsed realtime price (체결가) message."""

    symbol_code: str
    price: str
    change_sign: str = ""
    change_amount: str = ""
    volume: str = ""
    trade_time: str = ""
    raw_tr_id: str = ""


class RealtimeOrderbookMessage(BaseModel):
    """Parsed realtime orderbook (호가) message."""

    symbol_code: str
    ask_price_1: str = ""
    ask_volume_1: str = ""
    bid_price_1: str = ""
    bid_volume_1: str = ""
    raw_tr_id: str = ""


class ExecutionNoticeMessage(BaseModel):
    """Parsed execution notice (체결통보) message."""

    symbol_code: str
    order_number: str = ""
    executed_quantity: str = ""
    executed_price: str = ""
    side: str = ""
    account_no: str = ""
    raw_tr_id: str = ""
