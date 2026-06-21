"""Repository serialization helpers."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.backtest.backtest_result import BacktestResult
from app.domain.order.order import Order
from app.domain.portfolio.cash_balance import CashBalance
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.portfolio.position import Position
from app.domain.risk.risk_policy import RiskPolicy
from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_state import StrategyState
from app.domain.strategy.strategy_statistics import StrategyStatistics
from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage


def utc_now_iso() -> str:
    return datetime.now().isoformat()


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def decode_json(value: str) -> Any:
    return json.loads(value)


def order_to_row(order: Order, *, created_at: str | None = None) -> dict[str, Any]:
    return {
        "order_number": order.order_number,
        "order_branch": order.order_branch,
        "symbol_code": order.symbol_code,
        "side": order.side,
        "quantity": order.quantity,
        "price": order.price,
        "status": order.status,
        "created_at": created_at or utc_now_iso(),
    }


def row_to_order(row: dict[str, Any]) -> Order:
    return Order(
        order_number=str(row["order_number"]),
        order_branch=str(row["order_branch"]),
        symbol_code=str(row["symbol_code"]),
        side=str(row["side"]),
        quantity=str(row["quantity"]),
        price=str(row["price"]),
        status=str(row["status"]),
    )


def position_to_row(position: Position, *, account_no: str, updated_at: str) -> dict[str, Any]:
    return {
        "account_no": account_no,
        "symbol_code": position.symbol_code,
        "stock_name": position.stock_name,
        "quantity": str(position.quantity),
        "average_price": str(position.average_price),
        "current_price": str(position.current_price),
        "updated_at": updated_at,
    }


def row_to_position(row: dict[str, Any]) -> Position:
    return Position(
        symbol_code=str(row["symbol_code"]),
        stock_name=str(row["stock_name"]),
        quantity=Decimal(str(row["quantity"])),
        average_price=Decimal(str(row["average_price"])),
        current_price=Decimal(str(row["current_price"])),
    )


def snapshot_to_row(snapshot: PortfolioSnapshot) -> dict[str, Any]:
    return {
        "account_no": snapshot.account_no,
        "total_asset": str(snapshot.total_asset),
        "total_evaluation": str(snapshot.total_evaluation),
        "total_profit_loss": str(snapshot.total_profit_loss),
        "profit_rate": str(snapshot.profit_rate),
        "cash_total": str(snapshot.cash.total_deposit),
        "cash_orderable": str(snapshot.cash.orderable_cash),
        "position_count": len(snapshot.positions),
        "snapshot_json": encode_json(
            {
                "total_purchase": str(snapshot.total_purchase),
                "positions": [
                    {
                        "symbol_code": item.symbol_code,
                        "stock_name": item.stock_name,
                        "quantity": str(item.quantity),
                        "average_price": str(item.average_price),
                        "current_price": str(item.current_price),
                    }
                    for item in snapshot.positions
                ],
            }
        ),
        "created_at": snapshot.updated_at.isoformat(),
    }


def row_to_snapshot(row: dict[str, Any]) -> PortfolioSnapshot:
    payload = decode_json(str(row.get("snapshot_json", "{}")))
    positions = tuple(
        Position(
            symbol_code=str(item["symbol_code"]),
            stock_name=str(item.get("stock_name", "")),
            quantity=Decimal(str(item["quantity"])),
            average_price=Decimal(str(item["average_price"])),
            current_price=Decimal(str(item["current_price"])),
        )
        for item in payload.get("positions", [])
    )
    return PortfolioSnapshot(
        account_no=str(row["account_no"]),
        cash=CashBalance(
            total_deposit=Decimal(str(row["cash_total"])),
            orderable_cash=Decimal(str(row["cash_orderable"])),
        ),
        positions=positions,
        total_evaluation=Decimal(str(row["total_evaluation"])),
        total_purchase=Decimal(str(payload.get("total_purchase", "0"))),
        total_profit_loss=Decimal(str(row["total_profit_loss"])),
        total_asset=Decimal(str(row["total_asset"])),
        profit_rate=Decimal(str(row["profit_rate"])),
        updated_at=datetime.fromisoformat(str(row["created_at"])),
    )


def strategy_to_row(
    strategy: Strategy, *, timestamps: dict[str, str] | None = None
) -> dict[str, Any]:
    now = utc_now_iso()
    stats = strategy.statistics
    statistics_payload = {}
    if stats is not None:
        statistics_payload = {
            "strategy_id": stats.strategy_id,
            "total_signals": stats.total_signals,
            "buy_signals": stats.buy_signals,
            "sell_signals": stats.sell_signals,
            "hold_signals": stats.hold_signals,
            "cancel_signals": stats.cancel_signals,
            "execution_count": stats.execution_count,
            "market_data_count": stats.market_data_count,
            "last_signal_at": stats.last_signal_at.isoformat() if stats.last_signal_at else None,
        }
    return {
        "strategy_id": strategy.strategy_id,
        "name": strategy.name,
        "strategy_type": strategy.strategy_type,
        "enabled": 1 if strategy.enabled else 0,
        "parameters_json": encode_json(strategy.parameters),
        "symbols_json": encode_json(list(strategy.symbols)),
        "state": strategy.state.value,
        "statistics_json": encode_json(statistics_payload),
        "created_at": (timestamps or {}).get("created_at", now),
        "updated_at": (timestamps or {}).get("updated_at", now),
    }


def row_to_strategy(row: dict[str, Any]) -> Strategy:
    stats_payload = decode_json(str(row.get("statistics_json", "{}")))
    statistics = None
    if stats_payload:
        last_signal_at = stats_payload.get("last_signal_at")
        statistics = StrategyStatistics(
            strategy_id=str(stats_payload.get("strategy_id", row["strategy_id"])),
            total_signals=int(stats_payload.get("total_signals", 0)),
            buy_signals=int(stats_payload.get("buy_signals", 0)),
            sell_signals=int(stats_payload.get("sell_signals", 0)),
            hold_signals=int(stats_payload.get("hold_signals", 0)),
            cancel_signals=int(stats_payload.get("cancel_signals", 0)),
            execution_count=int(stats_payload.get("execution_count", 0)),
            market_data_count=int(stats_payload.get("market_data_count", 0)),
            last_signal_at=datetime.fromisoformat(last_signal_at) if last_signal_at else None,
        )
    return Strategy(
        strategy_id=str(row["strategy_id"]),
        name=str(row["name"]),
        strategy_type=str(row["strategy_type"]),
        enabled=bool(row["enabled"]),
        parameters=decode_json(str(row["parameters_json"])),
        symbols=tuple(decode_json(str(row["symbols_json"]))),
        state=StrategyState(str(row["state"])),
        statistics=statistics,
    )


def risk_policy_to_row(
    policy: RiskPolicy, *, policy_name: str, updated_at: str | None = None
) -> dict[str, Any]:
    return {
        "policy_name": policy_name,
        "max_order_amount": str(policy.max_order_amount),
        "max_order_quantity": str(policy.max_order_quantity),
        "max_position_count": policy.max_position_count,
        "max_symbol_weight": str(policy.max_symbol_weight),
        "daily_loss_limit": str(policy.daily_loss_limit),
        "duplicate_order_block": 1 if policy.duplicate_order_block else 0,
        "emergency_stop": 1 if policy.emergency_stop else 0,
        "updated_at": updated_at or utc_now_iso(),
    }


def row_to_risk_policy(row: dict[str, Any]) -> RiskPolicy:
    return RiskPolicy(
        max_order_amount=Decimal(str(row["max_order_amount"])),
        max_order_quantity=Decimal(str(row["max_order_quantity"])),
        max_position_count=int(row["max_position_count"]),
        max_symbol_weight=Decimal(str(row["max_symbol_weight"])),
        daily_loss_limit=Decimal(str(row["daily_loss_limit"])),
        duplicate_order_block=bool(row["duplicate_order_block"]),
        emergency_stop=bool(row["emergency_stop"]),
    )


def backtest_to_row(
    result: BacktestResult,
    *,
    strategy_type: str,
    strategy_name: str,
    symbols: list[str],
    created_at: str | None = None,
) -> dict[str, Any]:
    return {
        "strategy_type": strategy_type,
        "strategy_name": strategy_name,
        "symbols_json": encode_json(symbols),
        "initial_capital": str(result.initial_capital),
        "final_asset": str(result.final_asset),
        "total_return_rate": str(result.total_return_rate),
        "win_rate": str(result.win_rate),
        "profit_loss_ratio": str(result.profit_loss_ratio),
        "profit_factor": str(result.profit_factor),
        "max_drawdown": str(result.max_drawdown),
        "trade_count": result.trade_count,
        "average_profit": str(result.average_profit),
        "average_loss": str(result.average_loss),
        "equity_curve_json": encode_json(
            [(timestamp.isoformat(), str(value)) for timestamp, value in result.equity_curve]
        ),
        "created_at": created_at or utc_now_iso(),
    }


def row_to_backtest(row: dict[str, Any]) -> BacktestResult:
    equity_payload = decode_json(str(row.get("equity_curve_json", "[]")))
    equity_curve = tuple(
        (datetime.fromisoformat(str(timestamp)), Decimal(str(value)))
        for timestamp, value in equity_payload
    )
    return BacktestResult(
        initial_capital=Decimal(str(row["initial_capital"])),
        final_asset=Decimal(str(row["final_asset"])),
        total_return_rate=Decimal(str(row["total_return_rate"])),
        win_rate=Decimal(str(row["win_rate"])),
        profit_loss_ratio=Decimal(str(row["profit_loss_ratio"])),
        profit_factor=Decimal(str(row["profit_factor"])),
        max_drawdown=Decimal(str(row["max_drawdown"])),
        trade_count=int(row["trade_count"]),
        average_profit=Decimal(str(row["average_profit"])),
        average_loss=Decimal(str(row["average_loss"])),
        equity_curve=equity_curve,
    )


def notification_to_row(message: NotificationMessage) -> dict[str, Any]:
    return {
        "notification_id": message.notification_id,
        "category": str(message.category),
        "title": message.title,
        "body": message.body,
        "level": message.level,
        "source_event": message.source_event,
        "context_json": encode_json(message.context),
        "created_at": message.created_at.isoformat(),
    }


def row_to_notification(row: dict[str, Any]) -> NotificationMessage:
    return NotificationMessage(
        notification_id=str(row["notification_id"]),
        category=NotificationCategory(str(row["category"])),
        title=str(row["title"]),
        body=str(row["body"]),
        level=str(row["level"]),
        source_event=str(row["source_event"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        context=decode_json(str(row.get("context_json", "{}"))),
    )
