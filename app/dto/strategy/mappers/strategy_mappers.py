"""Strategy DTO mappers."""

from __future__ import annotations

from decimal import Decimal

from app.domain.strategy.signal_result import SignalResult
from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_statistics import StrategyStatistics
from app.domain.strategy.trading_signal import TradingSignal
from app.dto.strategy.signal_dto import SignalDto
from app.dto.strategy.statistics_dto import StatisticsDto
from app.dto.strategy.strategy_dto import StrategyDto
from app.dto.strategy.strategy_result_dto import StrategyResultDto


class StrategyMapper:
    """Maps between ``Strategy`` entity and ``StrategyDto``."""

    @staticmethod
    def to_dto(entity: Strategy) -> StrategyDto:
        """Convert entity to DTO."""
        return StrategyDto(
            strategy_id=entity.strategy_id,
            name=entity.name,
            strategy_type=entity.strategy_type,
            enabled=entity.enabled,
            parameters=dict(entity.parameters),
            symbols=list(entity.symbols),
            state=entity.state.value,
        )

    @staticmethod
    def to_entity(dto: StrategyDto) -> Strategy:
        """Convert DTO to entity."""
        from app.domain.strategy.strategy_state import StrategyState

        return Strategy(
            strategy_id=dto.strategy_id,
            name=dto.name,
            strategy_type=dto.strategy_type,
            enabled=dto.enabled,
            parameters=dict(dto.parameters),
            symbols=tuple(dto.symbols),
            state=StrategyState(dto.state),
        )


class SignalMapper:
    """Maps between ``TradingSignal`` entity and ``SignalDto``."""

    @staticmethod
    def to_dto(entity: TradingSignal) -> SignalDto:
        """Convert entity to DTO."""
        return SignalDto(
            signal_id=entity.signal_id,
            strategy_id=entity.strategy_id,
            strategy_name=entity.strategy_name,
            symbol_code=entity.symbol_code,
            signal_type=entity.signal_type.value,
            price=str(entity.price),
            quantity=str(entity.quantity),
            confidence=str(entity.confidence),
            timestamp=entity.timestamp.isoformat(),
            reason=entity.reason,
        )

    @staticmethod
    def to_entity(dto: SignalDto) -> TradingSignal:
        """Convert DTO to entity."""
        from datetime import datetime

        from app.domain.strategy.trading_signal import SignalType

        return TradingSignal(
            signal_id=dto.signal_id,
            strategy_id=dto.strategy_id,
            strategy_name=dto.strategy_name,
            symbol_code=dto.symbol_code,
            signal_type=SignalType(dto.signal_type),
            price=Decimal(dto.price),
            quantity=Decimal(dto.quantity),
            confidence=Decimal(dto.confidence),
            timestamp=datetime.fromisoformat(dto.timestamp),
            reason=dto.reason,
        )


class StatisticsMapper:
    """Maps between ``StrategyStatistics`` entity and ``StatisticsDto``."""

    @staticmethod
    def to_dto(entity: StrategyStatistics) -> StatisticsDto:
        """Convert entity to DTO."""
        return StatisticsDto(
            strategy_id=entity.strategy_id,
            total_signals=entity.total_signals,
            buy_signals=entity.buy_signals,
            sell_signals=entity.sell_signals,
            hold_signals=entity.hold_signals,
            cancel_signals=entity.cancel_signals,
            execution_count=entity.execution_count,
            market_data_count=entity.market_data_count,
            last_signal_at=entity.last_signal_at.isoformat() if entity.last_signal_at else None,
        )


class StrategyResultMapper:
    """Maps ``SignalResult`` to ``StrategyResultDto``."""

    @staticmethod
    def to_dto(
        result: SignalResult,
        *,
        strategy_id: str = "",
        strategy_name: str = "",
        statistics: StrategyStatistics | None = None,
    ) -> StrategyResultDto:
        """Convert evaluation result to DTO."""
        signal_dto = SignalMapper.to_dto(result.signal) if result.signal else None
        stats_payload: dict[str, int] = {}
        if statistics is not None:
            stats_payload = {
                "total_signals": statistics.total_signals,
                "buy_signals": statistics.buy_signals,
                "sell_signals": statistics.sell_signals,
                "hold_signals": statistics.hold_signals,
                "cancel_signals": statistics.cancel_signals,
            }
        return StrategyResultDto(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            evaluated=result.evaluated,
            accepted=result.accepted,
            message=result.message,
            signal=signal_dto,
            statistics=stats_payload,
        )
