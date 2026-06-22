"""Centralized trade blotter status mapping."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.domain.trade_blotter.trade_blotter_item import TradeBlotterStatus
from app.dto.order.order_constants import ORDER_DIVISION_LIMIT, ORDER_DIVISION_MARKET

_SIDE_LABELS = {
    "01": "SELL",
    "02": "BUY",
    "sell": "SELL",
    "buy": "BUY",
}

_ORDER_DIVISION_LABELS = {
    ORDER_DIVISION_LIMIT: "LIMIT",
    ORDER_DIVISION_MARKET: "MARKET",
    "00": "LIMIT",
    "01": "MARKET",
}


def map_order_side_label(side_code: str) -> str:
    """Map KIS side code to BUY/SELL label."""
    normalized = side_code.strip().lower()
    if normalized in {"sell", "buy"}:
        return normalized.upper()
    return _SIDE_LABELS.get(side_code.strip(), side_code.strip() or "-")


def map_order_division_label(order_division: str) -> str:
    """Map KIS order division code to a display label."""
    return _ORDER_DIVISION_LABELS.get(order_division.strip(), order_division.strip() or "-")


def map_trade_blotter_status(
    *,
    order_quantity: str,
    filled_quantity: str,
    remaining_quantity: str,
    cancel_yn: str,
    reject_reason: str,
) -> TradeBlotterStatus:
    """Normalize broker-specific order states into blotter statuses."""
    if cancel_yn.strip().upper() == "Y":
        return "CANCELLED"
    if reject_reason.strip():
        return "REJECTED"

    order_qty = _parse_decimal(order_quantity)
    filled_qty = _parse_decimal(filled_quantity)
    remaining_qty = _parse_decimal(remaining_quantity)

    if order_qty <= 0 and filled_qty <= 0:
        return "NEW"
    if filled_qty <= 0:
        return "ACCEPTED"
    if order_qty > 0 and filled_qty < order_qty and remaining_qty > 0:
        return "PARTIALLY_FILLED"
    if order_qty > 0 and filled_qty >= order_qty:
        return "FILLED"
    if filled_qty > 0:
        return "FILLED"
    return "ACCEPTED"


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")
