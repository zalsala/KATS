"""Order request helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.account.value_objects.account_context import AccountContext


class OrderRequestBase(BaseModel):
    """Base request fields for order APIs."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    account: AccountContext

    def base_body(self) -> dict[str, str]:
        """Return CANO and ACNT_PRDT_CD body fields."""
        return self.account.to_base_params()


class CashBuyOrderRequest(OrderRequestBase):
    """Cash buy order request."""

    symbol_code: str
    quantity: str
    price: str
    order_division: str = Field(default="00", description="00: limit order")

    def to_body(self) -> dict[str, str]:
        """Convert to KIS order-cash request body."""
        body = self.base_body()
        body.update(
            {
                "PDNO": self.symbol_code,
                "ORD_DVSN": self.order_division,
                "ORD_QTY": self.quantity,
                "ORD_UNPR": self.price,
                "SLL_BUY_DVSN_CD": "02",
                "EXCG_ID_DVSN_CD": "KRX",
            }
        )
        return body


class CashSellOrderRequest(OrderRequestBase):
    """Cash sell order request."""

    symbol_code: str
    quantity: str
    price: str
    order_division: str = Field(default="00", description="00: limit order")

    def to_body(self) -> dict[str, str]:
        """Convert to KIS order-cash request body."""
        body = self.base_body()
        body.update(
            {
                "PDNO": self.symbol_code,
                "ORD_DVSN": self.order_division,
                "ORD_QTY": self.quantity,
                "ORD_UNPR": self.price,
                "SLL_BUY_DVSN_CD": "01",
                "EXCG_ID_DVSN_CD": "KRX",
            }
        )
        return body


class ModifyOrderRequest(OrderRequestBase):
    """Modify order request."""

    order_branch: str
    original_order_number: str
    quantity: str
    price: str
    order_division: str = "00"
    cancel_all: bool = False

    def to_body(self) -> dict[str, str]:
        """Convert to KIS order-rvsecncl modify body."""
        body = self.base_body()
        body.update(
            {
                "KRX_FWDG_ORD_ORGNO": self.order_branch,
                "ORGN_ODNO": self.original_order_number,
                "ORD_DVSN": self.order_division,
                "RVSE_CNCL_DVSN_CD": "01",
                "ORD_QTY": "0" if self.cancel_all else self.quantity,
                "ORD_UNPR": self.price,
                "QTY_ALL_ORD_YN": "Y" if self.cancel_all else "N",
                "EXCG_ID_DVSN_CD": "KRX",
            }
        )
        return body


class CancelOrderRequest(OrderRequestBase):
    """Cancel order request."""

    order_branch: str
    original_order_number: str
    quantity: str = "0"
    order_division: str = "00"
    cancel_all: bool = True

    def to_body(self) -> dict[str, str]:
        """Convert to KIS order-rvsecncl cancel body."""
        body = self.base_body()
        body.update(
            {
                "KRX_FWDG_ORD_ORGNO": self.order_branch,
                "ORGN_ODNO": self.original_order_number,
                "ORD_DVSN": self.order_division,
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": "0" if self.cancel_all else self.quantity,
                "ORD_UNPR": "0",
                "QTY_ALL_ORD_YN": "Y" if self.cancel_all else "N",
                "EXCG_ID_DVSN_CD": "KRX",
            }
        )
        return body
