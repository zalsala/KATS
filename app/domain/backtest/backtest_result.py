"""Backtest performance result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Aggregated backtest performance metrics."""

    initial_capital: Decimal
    final_asset: Decimal
    total_return_rate: Decimal
    win_rate: Decimal
    profit_loss_ratio: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    trade_count: int
    average_profit: Decimal
    average_loss: Decimal
    equity_curve: tuple[tuple[datetime, Decimal], ...]
