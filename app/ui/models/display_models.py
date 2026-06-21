"""UI-facing display data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PortfolioSummary:
    """Portfolio summary for dashboard and portfolio views."""

    account_no: str
    total_asset: Decimal
    total_evaluation: Decimal
    total_profit_loss: Decimal
    profit_rate: Decimal
    cash: Decimal
    position_count: int


@dataclass(frozen=True, slots=True)
class PositionRow:
    """Single row in the holdings table."""

    symbol_code: str
    stock_name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    evaluation_amount: Decimal
    profit_loss_amount: Decimal
    profit_loss_rate: Decimal


@dataclass(frozen=True, slots=True)
class StrategyRow:
    """Single row in the strategy table."""

    strategy_id: str
    name: str
    strategy_type: str
    state: str
    enabled: bool
    symbols: str


@dataclass(frozen=True, slots=True)
class OrderFormData:
    """Order form input data."""

    symbol_code: str
    quantity: str
    price: str
    side: str = "buy"


@dataclass(frozen=True, slots=True)
class BacktestDisplayResult:
    """Backtest result formatted for UI."""

    total_return_rate: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    trade_count: int
    final_asset: Decimal


@dataclass(frozen=True, slots=True)
class LogEntry:
    """Log panel entry."""

    timestamp: datetime
    level: str
    message: str
