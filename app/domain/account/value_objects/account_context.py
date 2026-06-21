"""Account query context value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.account.exceptions import InvalidAccountContextError

ACCOUNT_NO_PATTERN = re.compile(r"^\d{8}$")
ACCOUNT_PRODUCT_PATTERN = re.compile(r"^\d{2}$")


@dataclass(frozen=True, slots=True)
class AccountContext:
    """KIS account query context.

    Attributes:
        account_no: Eight-digit account number (CANO).
        account_product: Two-digit account product code (ACNT_PRDT_CD).
    """

    account_no: str
    account_product: str = "01"

    def __post_init__(self) -> None:
        if not ACCOUNT_NO_PATTERN.match(self.account_no):
            msg = f"Invalid account number: {self.account_no}"
            raise InvalidAccountContextError(msg)
        if not ACCOUNT_PRODUCT_PATTERN.match(self.account_product):
            msg = f"Invalid account product code: {self.account_product}"
            raise InvalidAccountContextError(msg)

    def to_base_params(self) -> dict[str, str]:
        """Return base KIS account query parameters."""
        return {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product,
        }
