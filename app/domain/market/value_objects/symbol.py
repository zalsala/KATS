"""Stock symbol value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.market.exceptions import InvalidSymbolError

SYMBOL_PATTERN = re.compile(r"^\d{6}$")


@dataclass(frozen=True, slots=True)
class Symbol:
    """KRX stock symbol (6-digit code).

    Attributes:
        code: Six-digit stock code such as ``005930``.
    """

    code: str

    def __post_init__(self) -> None:
        normalized = self.code.strip()
        if not SYMBOL_PATTERN.match(normalized):
            msg = f"Invalid stock symbol: {self.code}"
            raise InvalidSymbolError(msg)
        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code
