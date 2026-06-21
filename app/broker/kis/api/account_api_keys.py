"""Account API registry keys for KIS OpenAPI."""

from __future__ import annotations

from typing import Final

INQUIRE_BALANCE: Final[str] = "account.inquire_balance"
INQUIRE_PSBL_ORDER: Final[str] = "account.inquire_psbl_order"
INQUIRE_DAILY_CCLD: Final[str] = "account.inquire_daily_ccld"

ACCOUNT_API_KEYS: Final[frozenset[str]] = frozenset(
    {
        INQUIRE_BALANCE,
        INQUIRE_PSBL_ORDER,
        INQUIRE_DAILY_CCLD,
    }
)
