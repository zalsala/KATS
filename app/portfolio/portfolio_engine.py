"""Portfolio calculation and event application engine."""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from app.domain.portfolio.cash_balance import CashBalance
from app.domain.portfolio.portfolio import Portfolio
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.portfolio.position import Position, _to_decimal
from app.events.domain_events import PortfolioEvent
from app.events.event_bus_service import EventBusService
from app.portfolio.in_memory_portfolio_store import InMemoryPortfolioStore

logger = logging.getLogger(__name__)

BUY_SIDE = "02"
SELL_SIDE = "01"


class PortfolioEngine:
    """Applies account, execution, and market events to portfolio state."""

    def __init__(
        self,
        *,
        store: InMemoryPortfolioStore,
        event_bus: EventBusService | None = None,
        source: str = "portfolio_engine",
        snapshot_listener: Callable[[PortfolioSnapshot], None] | None = None,
    ) -> None:
        self._store = store
        self._event_bus = event_bus
        self._source = source
        self._snapshot_listener = snapshot_listener

    def apply_account(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply account balance and holdings from an AccountEvent payload."""
        account_no = str(payload.get("account_no", self._store.get().account_no))
        cash = CashBalance(
            total_deposit=_to_decimal(payload.get("total_deposit", "0")),
            orderable_cash=_to_decimal(payload.get("orderable_cash", "0")),
        )
        holdings = payload.get("holdings", [])
        positions: dict[str, Position] = {}
        if isinstance(holdings, list):
            for item in holdings:
                if isinstance(item, dict):
                    position = Position.from_payload(item)
                    if position.symbol_code and position.quantity > 0:
                        positions[position.symbol_code] = position

        def _update(portfolio: Portfolio) -> None:
            portfolio.account_no = account_no
            portfolio.cash = cash
            portfolio.positions = positions

        snapshot = self._store.update(_update)
        self._publish_portfolio_event("account_sync", snapshot)
        self._notify_snapshot_listener(snapshot)
        return snapshot

    def apply_execution(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply an execution fill to portfolio positions."""
        symbol_code = str(payload.get("symbol_code", ""))
        side = str(payload.get("side", ""))
        quantity = _to_decimal(payload.get("executed_quantity", "0"))
        price = _to_decimal(payload.get("executed_price", "0"))
        stock_name = str(payload.get("stock_name", symbol_code))

        def _update(portfolio: Portfolio) -> None:
            current = portfolio.positions.get(symbol_code)
            if side == BUY_SIDE:
                if current is None:
                    portfolio.positions[symbol_code] = Position(
                        symbol_code=symbol_code,
                        stock_name=stock_name,
                        quantity=quantity,
                        average_price=price,
                        current_price=price,
                    )
                else:
                    portfolio.positions[symbol_code] = current.apply_buy(quantity, price)
            elif side == SELL_SIDE and current is not None:
                updated = current.apply_sell(quantity)
                if updated is None:
                    del portfolio.positions[symbol_code]
                else:
                    portfolio.positions[symbol_code] = updated

        snapshot = self._store.update(_update)
        self._publish_portfolio_event("execution_applied", snapshot)
        self._notify_snapshot_listener(snapshot)
        return snapshot

    def apply_market_data(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Update current prices from a market data event payload."""
        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        price = _to_decimal(payload.get("price", payload.get("current_price", "0")))

        def _update(portfolio: Portfolio) -> None:
            current = portfolio.positions.get(symbol_code)
            if current is not None:
                portfolio.positions[symbol_code] = current.with_price(price)

        snapshot = self._store.update(_update)
        self._publish_portfolio_event("market_data_applied", snapshot)
        self._notify_snapshot_listener(snapshot)
        return snapshot

    def get_snapshot(self) -> PortfolioSnapshot:
        """Return the current portfolio snapshot."""
        return self._store.snapshot()

    def adjust_cash(self, delta: Decimal) -> PortfolioSnapshot:
        """Adjust cash balance by delta amount."""

        def _update(portfolio: Portfolio) -> None:
            portfolio.cash = CashBalance(
                total_deposit=portfolio.cash.total_deposit + delta,
                orderable_cash=portfolio.cash.orderable_cash + delta,
            )

        snapshot = self._store.update(_update)
        self._publish_portfolio_event("cash_adjusted", snapshot)
        self._notify_snapshot_listener(snapshot)
        return snapshot

    def _notify_snapshot_listener(self, snapshot: PortfolioSnapshot) -> None:
        if self._snapshot_listener is None:
            return
        self._snapshot_listener(snapshot)

    def _publish_portfolio_event(self, reason: str, snapshot: PortfolioSnapshot) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            PortfolioEvent(
                source=self._source,
                event_name="portfolio.updated",
                payload={
                    "reason": reason,
                    "account_no": snapshot.account_no,
                    "total_asset": str(snapshot.total_asset),
                    "total_evaluation": str(snapshot.total_evaluation),
                    "total_profit_loss": str(snapshot.total_profit_loss),
                    "profit_rate": str(snapshot.profit_rate),
                    "position_count": len(snapshot.positions),
                },
                correlation_id=snapshot.updated_at.isoformat(),
            )
        )
        logger.info(
            "Portfolio updated reason=%s total_asset=%s profit_rate=%s",
            reason,
            snapshot.total_asset,
            snapshot.profit_rate,
        )
