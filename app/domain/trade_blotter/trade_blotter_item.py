"""Trade blotter row model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.domain.account.entities.trade_history import TradeHistory
from app.dto.account.trade_history_dto import TradeHistoryDto
from app.order.trade_blotter_status_mapper import (
    map_order_division_label,
    map_order_side_label,
    map_trade_blotter_status,
)

TradeBlotterStatus = Literal[
    "NEW",
    "ACCEPTED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
]

OPEN_STATUSES: frozenset[TradeBlotterStatus] = frozenset(
    {"NEW", "ACCEPTED", "PARTIALLY_FILLED"},
)


@dataclass(frozen=True, slots=True)
class TradeBlotterItem:
    """Normalized domestic stock order and execution row."""

    order_time: str
    order_date: str
    symbol_code: str
    stock_name: str
    side: str
    order_type: str
    order_quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    order_price: Decimal
    average_fill_price: Decimal
    status: TradeBlotterStatus
    order_number: str

    @classmethod
    def from_trade_history_dto(cls, dto: TradeHistoryDto) -> TradeBlotterItem:
        order_quantity = _to_decimal(dto.order_quantity or dto.executed_quantity)
        filled_quantity = _to_decimal(dto.executed_quantity)
        remaining_quantity = _to_decimal(dto.remaining_quantity)
        if remaining_quantity <= 0 and order_quantity > filled_quantity:
            remaining_quantity = order_quantity - filled_quantity
        status = map_trade_blotter_status(
            order_quantity=dto.order_quantity,
            filled_quantity=dto.executed_quantity,
            remaining_quantity=dto.remaining_quantity,
            cancel_yn=dto.cancel_yn,
            reject_reason=dto.reject_reason,
        )
        return cls(
            order_time=dto.order_time,
            order_date=dto.order_date,
            symbol_code=dto.symbol_code,
            stock_name=dto.stock_name,
            side=map_order_side_label(dto.side),
            order_type=map_order_division_label(dto.order_division),
            order_quantity=order_quantity,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            order_price=_to_decimal(dto.order_price),
            average_fill_price=_to_decimal(dto.executed_price),
            status=status,
            order_number=dto.order_number,
        )

    @property
    def sort_key(self) -> tuple[str, str]:
        """Return a descending sort key for newest-first ordering."""
        return (self.order_date, self.order_time)

    def with_execution(
        self,
        *,
        execution_quantity: Decimal,
        execution_price: Decimal,
    ) -> TradeBlotterItem:
        """Apply a realtime execution fill to this row."""
        new_filled = self.filled_quantity + execution_quantity
        if new_filled > self.order_quantity and self.order_quantity > 0:
            new_filled = self.order_quantity
        if new_filled > 0 and execution_quantity > 0:
            prior_value = self.average_fill_price * self.filled_quantity
            fill_value = execution_price * execution_quantity
            new_average = (prior_value + fill_value) / new_filled
        else:
            new_average = execution_price
        new_remaining = max(self.order_quantity - new_filled, Decimal("0"))
        status = map_trade_blotter_status(
            order_quantity=str(self.order_quantity),
            filled_quantity=str(new_filled),
            remaining_quantity=str(new_remaining),
            cancel_yn="N",
            reject_reason="",
        )
        return TradeBlotterItem(
            order_time=self.order_time,
            order_date=self.order_date,
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            side=self.side,
            order_type=self.order_type,
            order_quantity=self.order_quantity,
            filled_quantity=new_filled,
            remaining_quantity=new_remaining,
            order_price=self.order_price,
            average_fill_price=new_average,
            status=status,
            order_number=self.order_number,
        )

    def with_status(self, status: TradeBlotterStatus) -> TradeBlotterItem:
        """Return a copy with an explicit status."""
        return TradeBlotterItem(
            order_time=self.order_time,
            order_date=self.order_date,
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            side=self.side,
            order_type=self.order_type,
            order_quantity=self.order_quantity,
            filled_quantity=self.filled_quantity,
            remaining_quantity=self.remaining_quantity,
            order_price=self.order_price,
            average_fill_price=self.average_fill_price,
            status=status,
            order_number=self.order_number,
        )


def _to_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value.replace(",", ""))
