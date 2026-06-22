"""Watchlist application service."""

from __future__ import annotations

import logging
from decimal import Decimal

from app.domain.market.exceptions import InvalidSymbolError
from app.domain.market.value_objects.symbol import Symbol
from app.domain.watchlist.watchlist_item import WatchlistItem
from app.repository.interfaces.watchlist_repository import (
    WatchlistRepository,
    WatchlistSnapshot,
    WatchlistSnapshotItem,
)
from app.service.market.market_service import MarketService

logger = logging.getLogger(__name__)


class WatchlistValidationError(Exception):
    """Raised when a watchlist symbol cannot be validated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class WatchlistService:
    """Manage watchlist validation and persistence."""

    def __init__(
        self,
        *,
        repository: WatchlistRepository,
        market_service: MarketService | None = None,
    ) -> None:
        self._repository = repository
        self._market_service = market_service

    def load_items(self) -> tuple[WatchlistItem, ...]:
        """Load persisted watchlist rows."""
        snapshot = self._repository.load()
        return tuple(self._to_runtime_item(item) for item in snapshot.items)

    def load_selected_symbol(self) -> str | None:
        """Load the persisted selected symbol."""
        return self._repository.load().selected_symbol

    def save_state(
        self,
        *,
        items: tuple[WatchlistItem, ...],
        selected_symbol: str | None,
    ) -> None:
        """Persist watchlist rows and selection."""
        snapshot = WatchlistSnapshot(
            selected_symbol=selected_symbol,
            items=tuple(
                WatchlistSnapshotItem(symbol_code=item.symbol_code, name=item.name)
                for item in items
            ),
        )
        self._repository.save(snapshot)

    def validate_symbol_code(self, symbol_code: str) -> str:
        """Validate symbol format and return the normalized code."""
        normalized = symbol_code.strip()
        try:
            return str(Symbol(normalized))
        except InvalidSymbolError as exc:
            raise WatchlistValidationError("Symbol must be a 6-digit stock code") from exc

    def resolve_symbol(self, symbol_code: str) -> WatchlistItem:
        """Validate symbol existence and build an initial watchlist row."""
        normalized = self.validate_symbol_code(symbol_code)
        if self._market_service is None:
            return WatchlistItem(symbol_code=normalized, name=normalized)

        try:
            quote = self._market_service.get_current_price(normalized)
        except Exception as exc:
            logger.exception("Market lookup failed for %s", normalized)
            msg = f"Unable to validate symbol: {normalized}"
            raise WatchlistValidationError(msg) from exc

        previous_close = quote.current_price - quote.change_amount
        return WatchlistItem(
            symbol_code=normalized,
            name=quote.stock_name,
            last_price=quote.current_price,
            change_amount=quote.change_amount,
            change_percent=quote.change_rate,
            previous_close=previous_close,
        )

    def _to_runtime_item(self, item: WatchlistSnapshotItem) -> WatchlistItem:
        if self._market_service is None:
            return WatchlistItem(symbol_code=item.symbol_code, name=item.name)

        try:
            return self.resolve_symbol(item.symbol_code)
        except WatchlistValidationError:
            logger.warning("Skipping quote refresh for persisted symbol %s", item.symbol_code)
            return WatchlistItem(symbol_code=item.symbol_code, name=item.name)

    @staticmethod
    def apply_live_price(item: WatchlistItem, price: Decimal) -> WatchlistItem:
        """Return an updated row using a realtime price tick."""
        updated = item.copy()
        updated.last_price = price
        updated.is_live = True
        if updated.previous_close is not None and updated.previous_close != 0:
            change_amount = price - updated.previous_close
            updated.change_amount = change_amount
            updated.change_percent = (change_amount / updated.previous_close) * Decimal("100")
        return updated
