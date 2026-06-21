"""UI controller — delegates all actions to services."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.backtest.historical_data_provider import HistoricalDataProvider
from app.domain.account.value_objects.account_context import AccountContext
from app.domain.backtest.backtest_result import BacktestResult
from app.domain.order.order_result import OrderResult
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.dto.order.order_requests import CashBuyOrderRequest, CashSellOrderRequest
from app.dto.strategy.strategy_dto import StrategyDto
from app.ui.context.ui_app_context import UiAppContext
from app.ui.models.display_models import (
    BacktestDisplayResult,
    LogEntry,
    OrderFormData,
    PortfolioSummary,
    PositionRow,
    StrategyRow,
)


class UiController:
    """Bridge between view models and application services."""

    def __init__(self, *, context: UiAppContext) -> None:
        self._context = context

    @property
    def context(self) -> UiAppContext:
        return self._context

    def get_connection_status(self) -> str:
        return "Connected" if self._context.is_connected else "Disconnected"

    def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        return self._context.portfolio_service.get_snapshot()

    def build_portfolio_summary(
        self, snapshot: PortfolioSnapshot | None = None
    ) -> PortfolioSummary:
        snap = snapshot or self.get_portfolio_snapshot()
        return PortfolioSummary(
            account_no=snap.account_no,
            total_asset=snap.total_asset,
            total_evaluation=snap.total_evaluation,
            total_profit_loss=snap.total_profit_loss,
            profit_rate=snap.profit_rate,
            cash=snap.cash.orderable_cash,
            position_count=len(snap.positions),
        )

    def build_position_rows(self, snapshot: PortfolioSnapshot | None = None) -> list[PositionRow]:
        snap = snapshot or self.get_portfolio_snapshot()
        return [
            PositionRow(
                symbol_code=position.symbol_code,
                stock_name=position.stock_name,
                quantity=position.quantity,
                average_price=position.average_price,
                current_price=position.current_price,
                evaluation_amount=position.evaluation_amount,
                profit_loss_amount=position.profit_loss_amount,
                profit_loss_rate=position.profit_loss_rate,
            )
            for position in snap.positions
        ]

    def refresh_portfolio_state(self) -> tuple[PortfolioSummary, list[PositionRow]]:
        snapshot = self.get_portfolio_snapshot()
        return self.build_portfolio_summary(snapshot), self.build_position_rows(snapshot)

    def submit_order(self, form: OrderFormData) -> OrderResult:
        if self._context.order_service is None:
            msg = "OrderService is not configured"
            raise RuntimeError(msg)
        account = self._resolve_account_context()
        if form.side == "buy":
            buy_request = CashBuyOrderRequest(
                account=account,
                symbol_code=form.symbol_code,
                quantity=form.quantity,
                price=form.price,
            )
            return self._context.order_service.place_cash_buy_order(buy_request)
        sell_request = CashSellOrderRequest(
            account=account,
            symbol_code=form.symbol_code,
            quantity=form.quantity,
            price=form.price,
        )
        return self._context.order_service.place_cash_sell_order(sell_request)

    def register_strategy(
        self,
        *,
        strategy_type: str,
        name: str,
        symbols: list[str],
        parameters: dict[str, Any] | None = None,
        auto_start: bool = False,
    ) -> StrategyDto:
        return self._context.strategy_service.register_strategy(
            strategy_type=strategy_type,
            name=name,
            symbols=symbols,
            parameters=parameters,
            auto_start=auto_start,
        )

    def start_strategy(self, strategy_id: str) -> StrategyDto:
        return self._context.strategy_service.start_strategy(strategy_id)

    def stop_strategy(self, strategy_id: str) -> StrategyDto:
        return self._context.strategy_service.stop_strategy(strategy_id)

    def list_strategy_rows(self) -> list[StrategyRow]:
        return [
            StrategyRow(
                strategy_id=item.strategy_id,
                name=item.name,
                strategy_type=item.strategy_type,
                state=item.state,
                enabled=item.enabled,
                symbols=",".join(item.symbols),
            )
            for item in self._context.strategy_service.list_strategies()
        ]

    def count_running_strategies(self) -> int:
        return sum(
            1
            for item in self._context.strategy_service.list_strategies()
            if item.state == "running"
        )

    def activate_emergency_stop(self) -> None:
        self._context.risk_service.set_emergency_stop(True)

    def deactivate_emergency_stop(self) -> None:
        self._context.risk_service.set_emergency_stop(False)

    def is_emergency_stop_active(self) -> bool:
        return self._context.risk_service.manager.emergency_stop

    def run_backtest(
        self,
        *,
        provider: HistoricalDataProvider,
        strategy_type: str,
        strategy_name: str,
        symbols: list[str],
        parameters: dict[str, Any] | None = None,
        initial_capital: Decimal | None = None,
    ) -> BacktestResult:
        return self._context.backtest_service.run_backtest(
            provider=provider,
            strategy_type=strategy_type,
            strategy_name=strategy_name,
            symbols=symbols,
            parameters=parameters,
            initial_capital=initial_capital,
        )

    @staticmethod
    def to_backtest_display(result: BacktestResult) -> BacktestDisplayResult:
        return BacktestDisplayResult(
            total_return_rate=result.total_return_rate,
            win_rate=result.win_rate,
            profit_factor=result.profit_factor,
            max_drawdown=result.max_drawdown,
            trade_count=result.trade_count,
            final_asset=result.final_asset,
        )

    def load_settings(self) -> tuple[str, str, str]:
        settings = self._context.config_manager.load()
        return (
            settings.environment,
            settings.secrets.account_type,
            settings.config.application.version,
        )

    @staticmethod
    def build_log_entry(*, level: str, message: str) -> LogEntry:
        return LogEntry(timestamp=datetime.now(UTC), level=level, message=message)

    def _resolve_account_context(self) -> AccountContext:
        settings = self._context.config_manager.load()
        account_no = settings.secrets.account_no or "12345678"
        return AccountContext(account_no=account_no, account_product="01")
