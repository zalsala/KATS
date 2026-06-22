"""Core order service: validate → call API → convert → store."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.broker.kis.api.order_api_keys import ORDER_CASH, ORDER_RVSECNL
from app.domain.order.order import Order
from app.domain.order.order_result import OrderResult
from app.dto.order.order_constants import ORDER_DIVISION_LIMIT, ORDER_DIVISION_MARKET
from app.dto.order.order_requests import (
    CancelOrderRequest,
    CashBuyOrderRequest,
    CashSellOrderRequest,
    ModifyOrderRequest,
)
from app.dto.order.order_responses import OrderResponse
from app.order.order_api_client import OrderApiClient

if TYPE_CHECKING:
    from app.repository.interfaces.order_repository import OrderRepository

logger = logging.getLogger(__name__)


class OrderValidationError(ValueError):
    """Raised when an order request fails validation."""


class OrderService:
    """Core order service: validate → call API → convert → store."""

    def __init__(
        self,
        *,
        order_api_client: OrderApiClient,
        order_repository: OrderRepository | None = None,
    ) -> None:
        self._client = order_api_client
        self._order_repository = order_repository
        self._orders: list[Order] = []

    @property
    def orders(self) -> tuple[Order, ...]:
        """Return stored orders (for EventBus / Portfolio integration)."""
        if self._order_repository is not None:
            return tuple(self._order_repository.list_all())
        return tuple(self._orders)

    def place_cash_buy_order(self, request: CashBuyOrderRequest) -> OrderResult:
        """Submit a cash buy order."""
        self._validate_cash_order(
            request.symbol_code,
            request.quantity,
            request.price,
            request.order_division,
        )
        return self._submit(
            api_key=ORDER_CASH,
            body=request.to_body(),
            side="buy",
            symbol_code=request.symbol_code,
            quantity=request.quantity,
            price=request.price,
        )

    def place_cash_sell_order(self, request: CashSellOrderRequest) -> OrderResult:
        """Submit a cash sell order."""
        self._validate_cash_order(
            request.symbol_code,
            request.quantity,
            request.price,
            request.order_division,
        )
        return self._submit(
            api_key=ORDER_CASH,
            body=request.to_body(),
            side="sell",
            symbol_code=request.symbol_code,
            quantity=request.quantity,
            price=request.price,
        )

    def modify_order(self, request: ModifyOrderRequest) -> OrderResult:
        """Modify an existing order."""
        self._validate_modify_cancel(
            request.order_branch,
            request.original_order_number,
            request.quantity,
            request.price,
            is_modify=True,
        )
        return self._submit(
            api_key=ORDER_RVSECNL,
            body=request.to_body(),
            side="modify",
            symbol_code="",
            quantity=request.quantity,
            price=request.price,
        )

    def cancel_order(self, request: CancelOrderRequest) -> OrderResult:
        """Cancel an existing order."""
        self._validate_modify_cancel(
            request.order_branch,
            request.original_order_number,
            request.quantity,
            "0",
            is_modify=False,
        )
        return self._submit(
            api_key=ORDER_RVSECNL,
            body=request.to_body(),
            side="cancel",
            symbol_code="",
            quantity=request.quantity,
            price="0",
        )

    def _submit(
        self,
        *,
        api_key: str,
        body: dict[str, str],
        side: str,
        symbol_code: str,
        quantity: str,
        price: str,
    ) -> OrderResult:
        result = self._client.post(api_key, body)
        response = OrderResponse.from_api_output(result.output)
        order_result = OrderResult(
            success=result.rt_cd == "0",
            order_number=response.order_number,
            order_branch=response.order_branch,
            order_time=response.order_time,
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=result.msg1,
        )
        if order_result.success:
            order = Order(
                order_number=response.order_number,
                order_branch=response.order_branch,
                symbol_code=symbol_code,
                side=side,
                quantity=quantity,
                price=price,
                status="submitted",
            )
            order_result.order = order
            if self._order_repository is not None:
                self._order_repository.save(order)
            else:
                self._orders.append(order)
            logger.info("Order stored: %s %s", side, response.order_number)
        return order_result

    @staticmethod
    def _validate_cash_order(
        symbol_code: str,
        quantity: str,
        price: str,
        order_division: str = ORDER_DIVISION_LIMIT,
    ) -> None:
        if not symbol_code:
            raise OrderValidationError("symbol_code is required")
        if not quantity or int(quantity) <= 0:
            raise OrderValidationError("quantity must be greater than 0")
        if order_division == ORDER_DIVISION_MARKET:
            if price != "0":
                raise OrderValidationError("market order price must be 0")
            return
        if not price or int(price) <= 0:
            raise OrderValidationError("price must be greater than 0")

    @staticmethod
    def _validate_modify_cancel(
        order_branch: str,
        original_order_number: str,
        quantity: str,
        price: str,
        *,
        is_modify: bool,
    ) -> None:
        if not order_branch:
            raise OrderValidationError("order_branch is required")
        if not original_order_number:
            raise OrderValidationError("original_order_number is required")
        if is_modify and (not price or int(price) <= 0):
            raise OrderValidationError("price must be greater than 0 for modify")
        if not is_modify:
            return
        if quantity and int(quantity) < 0:
            raise OrderValidationError("quantity must not be negative")


def build_order_service(*, order_api_client: OrderApiClient) -> OrderService:
    """Create an OrderService wired with the given API client."""
    return OrderService(order_api_client=order_api_client)
