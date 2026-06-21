"""Unit tests for Symbol value object."""

from __future__ import annotations

import pytest

from app.domain.market.exceptions import InvalidSymbolError
from app.domain.market.value_objects.symbol import Symbol

pytestmark = pytest.mark.unit


class TestSymbol:
    """Tests for Symbol."""

    def test_valid_symbol(self) -> None:
        """Valid six-digit symbol is accepted."""
        symbol = Symbol("005930")

        assert str(symbol) == "005930"

    def test_invalid_symbol_raises(self) -> None:
        """Invalid symbol format raises InvalidSymbolError."""
        with pytest.raises(InvalidSymbolError):
            Symbol("ABC")
