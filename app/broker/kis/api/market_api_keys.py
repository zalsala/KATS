"""Market API registry keys for KIS OpenAPI."""

from __future__ import annotations

from typing import Final

INQUIRE_PRICE: Final[str] = "domestic_stock.inquire_price"
INQUIRE_ASKING_PRICE: Final[str] = "domestic_stock.inquire_asking_price"

MARKET_QUOTATION_API_KEYS: Final[frozenset[str]] = frozenset({INQUIRE_PRICE, INQUIRE_ASKING_PRICE})
