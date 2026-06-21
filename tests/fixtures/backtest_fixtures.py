"""Shared fixtures for backtest tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.backtest.historical_data_provider import HistoricalDataProvider
from app.domain.risk.risk_policy import RiskPolicy


def build_sample_provider(*, symbol: str = "005930") -> HistoricalDataProvider:
    """Build ascending price series for backtests."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    prices = [
        (base.replace(day=1), Decimal("70000")),
        (base.replace(day=2), Decimal("71000")),
        (base.replace(day=3), Decimal("72000")),
        (base.replace(day=4), Decimal("73000")),
        (base.replace(day=5), Decimal("74000")),
    ]
    return HistoricalDataProvider.from_prices(symbol_code=symbol, prices=prices)


def build_permissive_risk_policy() -> RiskPolicy:
    """Build permissive risk policy for backtest integration."""
    return RiskPolicy(
        max_order_amount=Decimal("100000000"),
        max_order_quantity=Decimal("1000"),
        max_position_count=10,
        max_symbol_weight=Decimal("1.0"),
        daily_loss_limit=Decimal("1.0"),
        duplicate_order_block=True,
        emergency_stop=False,
    )
