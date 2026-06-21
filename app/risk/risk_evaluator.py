"""Risk rule evaluator."""

from __future__ import annotations

from decimal import Decimal

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.risk.risk_policy import RiskPolicy
from app.domain.risk.risk_result import RiskResult
from app.domain.risk.risk_violation import RiskViolation
from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.risk.risk_manager import RiskManager


class RiskEvaluator:
    """Evaluates trading signals against configured risk rules."""

    def evaluate(
        self,
        signal: TradingSignal,
        *,
        portfolio: PortfolioSnapshot,
        policy: RiskPolicy,
        manager: RiskManager,
    ) -> RiskResult:
        """Run all risk rules and return the combined result."""
        manager.ensure_daily_baseline(portfolio.total_asset)

        if signal.signal_type == SignalType.HOLD:
            return RiskResult(
                approved=True,
                signal_id=signal.signal_id,
                symbol_code=signal.symbol_code,
                signal_type=signal.signal_type.value,
                violations=(),
                message="hold_signal_no_order_required",
            )

        violations: list[RiskViolation] = []
        violations.extend(self._check_emergency_stop(policy, manager))
        violations.extend(self._check_daily_loss_limit(portfolio, policy, manager))
        violations.extend(self._check_max_order_amount(signal, policy))
        violations.extend(self._check_max_order_quantity(signal, policy))

        if signal.signal_type == SignalType.BUY:
            violations.extend(self._check_insufficient_cash(signal, portfolio))
            violations.extend(self._check_max_position_count(signal, portfolio, policy))
            violations.extend(self._check_max_symbol_weight(signal, portfolio, policy))

        if policy.duplicate_order_block and signal.signal_type in {
            SignalType.BUY,
            SignalType.SELL,
        }:
            violations.extend(self._check_duplicate_order(signal, manager))

        approved = len(violations) == 0
        return RiskResult(
            approved=approved,
            signal_id=signal.signal_id,
            symbol_code=signal.symbol_code,
            signal_type=signal.signal_type.value,
            violations=tuple(violations),
            message="approved" if approved else "rejected",
        )

    def _check_emergency_stop(
        self,
        policy: RiskPolicy,
        manager: RiskManager,
    ) -> list[RiskViolation]:
        if policy.emergency_stop or manager.emergency_stop:
            return [
                RiskViolation(
                    rule_code="emergency_stop",
                    message="Emergency stop is active",
                )
            ]
        return []

    def _check_daily_loss_limit(
        self,
        portfolio: PortfolioSnapshot,
        policy: RiskPolicy,
        manager: RiskManager,
    ) -> list[RiskViolation]:
        loss_ratio = manager.daily_loss_ratio(portfolio.total_asset)
        if loss_ratio >= policy.daily_loss_limit:
            return [
                RiskViolation(
                    rule_code="daily_loss_limit",
                    message=(
                        f"Daily loss ratio {loss_ratio} exceeds limit {policy.daily_loss_limit}"
                    ),
                )
            ]
        return []

    def _check_max_order_amount(
        self,
        signal: TradingSignal,
        policy: RiskPolicy,
    ) -> list[RiskViolation]:
        order_amount = signal.price * signal.quantity
        if order_amount > policy.max_order_amount:
            return [
                RiskViolation(
                    rule_code="max_order_amount",
                    message=f"Order amount {order_amount} exceeds max {policy.max_order_amount}",
                )
            ]
        return []

    def _check_max_order_quantity(
        self,
        signal: TradingSignal,
        policy: RiskPolicy,
    ) -> list[RiskViolation]:
        if signal.quantity > policy.max_order_quantity:
            return [
                RiskViolation(
                    rule_code="max_order_quantity",
                    message=(
                        f"Order quantity {signal.quantity} exceeds max {policy.max_order_quantity}"
                    ),
                )
            ]
        return []

    def _check_insufficient_cash(
        self,
        signal: TradingSignal,
        portfolio: PortfolioSnapshot,
    ) -> list[RiskViolation]:
        order_amount = signal.price * signal.quantity
        if order_amount > portfolio.cash.orderable_cash:
            return [
                RiskViolation(
                    rule_code="insufficient_cash",
                    message=(
                        f"Order amount {order_amount} exceeds orderable cash "
                        f"{portfolio.cash.orderable_cash}"
                    ),
                )
            ]
        return []

    def _check_max_position_count(
        self,
        signal: TradingSignal,
        portfolio: PortfolioSnapshot,
        policy: RiskPolicy,
    ) -> list[RiskViolation]:
        held_symbols = {position.symbol_code for position in portfolio.positions}
        is_new_symbol = signal.symbol_code not in held_symbols
        projected_count = len(held_symbols) + (1 if is_new_symbol else 0)
        if projected_count > policy.max_position_count:
            return [
                RiskViolation(
                    rule_code="max_position_count",
                    message=(
                        f"Projected position count {projected_count} exceeds max "
                        f"{policy.max_position_count}"
                    ),
                )
            ]
        return []

    def _check_max_symbol_weight(
        self,
        signal: TradingSignal,
        portfolio: PortfolioSnapshot,
        policy: RiskPolicy,
    ) -> list[RiskViolation]:
        if portfolio.total_asset <= 0:
            return []

        current_eval = Decimal("0")
        for position in portfolio.positions:
            if position.symbol_code == signal.symbol_code:
                current_eval = position.evaluation_amount
                break

        projected_eval = current_eval + (signal.price * signal.quantity)
        weight = projected_eval / portfolio.total_asset
        if weight > policy.max_symbol_weight:
            return [
                RiskViolation(
                    rule_code="max_symbol_weight",
                    message=(
                        f"Projected symbol weight {weight} exceeds max {policy.max_symbol_weight}"
                    ),
                )
            ]
        return []

    def _check_duplicate_order(
        self,
        signal: TradingSignal,
        manager: RiskManager,
    ) -> list[RiskViolation]:
        if manager.has_pending_order(signal.symbol_code):
            return [
                RiskViolation(
                    rule_code="duplicate_order",
                    message=f"Duplicate order blocked for symbol {signal.symbol_code}",
                )
            ]
        return []
