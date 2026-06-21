"""Sample historical data for UI and tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.backtest.historical_data_provider import HistoricalDataProvider


def build_sample_price_provider(*, symbol_code: str = "005930") -> HistoricalDataProvider:
    """Build a small ascending price series."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    prices = [
        (base.replace(day=1), Decimal("70000")),
        (base.replace(day=2), Decimal("71000")),
        (base.replace(day=3), Decimal("72000")),
        (base.replace(day=4), Decimal("73000")),
        (base.replace(day=5), Decimal("74000")),
    ]
    return HistoricalDataProvider.from_prices(symbol_code=symbol_code, prices=prices)
