"""Backtest performance analyzer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.backtest.backtest_result import BacktestResult
from app.domain.backtest.virtual_trade import VirtualTrade


class PerformanceAnalyzer:
    """Calculates backtest performance metrics."""

    def __init__(self, *, initial_capital: Decimal) -> None:
        self._initial_capital = initial_capital
        self._trades: list[VirtualTrade] = []
        self._equity_curve: list[tuple[datetime, Decimal]] = []
        self._peak_equity = initial_capital

    @property
    def trades(self) -> tuple[VirtualTrade, ...]:
        """Return recorded virtual trades."""
        return tuple(self._trades)

    def record_trade(
        self,
        *,
        symbol_code: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        timestamp: datetime,
        realized_pnl: Decimal = Decimal("0"),
    ) -> None:
        """Record a completed virtual trade."""
        self._trades.append(
            VirtualTrade(
                trade_id=str(uuid4()),
                symbol_code=symbol_code,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=timestamp,
                realized_pnl=realized_pnl,
            )
        )

    def record_equity(self, timestamp: datetime, total_asset: Decimal) -> None:
        """Record equity curve point."""
        self._equity_curve.append((timestamp, total_asset))
        if total_asset > self._peak_equity:
            self._peak_equity = total_asset

    def finalize(self, final_asset: Decimal) -> BacktestResult:
        """Compute aggregated performance metrics."""
        closed_pnls = [trade.realized_pnl for trade in self._trades if trade.realized_pnl != 0]
        wins = [pnl for pnl in closed_pnls if pnl > 0]
        losses = [pnl for pnl in closed_pnls if pnl < 0]

        gross_profit = sum(wins, Decimal("0"))
        gross_loss = abs(sum(losses, Decimal("0")))

        average_profit = gross_profit / Decimal(len(wins)) if wins else Decimal("0")
        average_loss = gross_loss / Decimal(len(losses)) if losses else Decimal("0")

        win_rate = (
            (Decimal(len(wins)) / Decimal(len(closed_pnls))) * Decimal("100")
            if closed_pnls
            else Decimal("0")
        )
        profit_loss_ratio = average_profit / average_loss if average_loss > 0 else Decimal("0")
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else Decimal("0")

        total_return_rate = Decimal("0")
        if self._initial_capital > 0:
            total_return_rate = (
                (final_asset - self._initial_capital) / self._initial_capital
            ) * Decimal("100")

        max_drawdown = self._calculate_max_drawdown()

        if not self._equity_curve:
            self._equity_curve.append((datetime.now(), final_asset))

        return BacktestResult(
            initial_capital=self._initial_capital,
            final_asset=final_asset,
            total_return_rate=total_return_rate,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            trade_count=len(closed_pnls),
            average_profit=average_profit,
            average_loss=average_loss,
            equity_curve=tuple(self._equity_curve),
        )

    def _calculate_max_drawdown(self) -> Decimal:
        if not self._equity_curve:
            return Decimal("0")

        peak = self._equity_curve[0][1]
        max_drawdown = Decimal("0")
        for _, equity in self._equity_curve:
            if equity > peak:
                peak = equity
            if peak > 0:
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        return max_drawdown * Decimal("100")
