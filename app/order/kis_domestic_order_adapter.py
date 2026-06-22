"""KIS domestic stock cash order adapter."""

from __future__ import annotations

from app.domain.account.value_objects.account_context import AccountContext
from app.domain.order.order_result import OrderResult
from app.dto.order.order_entry_request import OrderEntryRequest
from app.dto.order.order_requests import CashBuyOrderRequest, CashSellOrderRequest
from app.service.order.order_service import OrderService


class KISDomesticOrderAdapter:
    """Adapter for KIS domestic stock cash order placement."""

    def __init__(self, *, order_service: OrderService) -> None:
        self._order_service = order_service

    def place_order(
        self,
        request: OrderEntryRequest,
        *,
        account: AccountContext,
    ) -> OrderResult:
        """Submit a domestic stock cash buy or sell order."""
        if request.side == "buy":
            return self._order_service.place_cash_buy_order(
                CashBuyOrderRequest(
                    account=account,
                    symbol_code=request.symbol_code,
                    quantity=request.quantity,
                    price=request.price,
                    order_division=request.order_division,
                )
            )
        return self._order_service.place_cash_sell_order(
            CashSellOrderRequest(
                account=account,
                symbol_code=request.symbol_code,
                quantity=request.quantity,
                price=request.price,
                order_division=request.order_division,
            )
        )
