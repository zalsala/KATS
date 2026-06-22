"""KIS domestic stock balance adapter."""

from __future__ import annotations

from app.domain.account.value_objects.account_context import AccountContext
from app.domain.position.position_item import PositionItem
from app.service.account.account_service import AccountService


class KISDomesticBalanceAdapter:
    """Adapter for KIS domestic stock balance and holdings inquiry."""

    def __init__(self, *, account_service: AccountService) -> None:
        self._account_service = account_service

    def get_positions(self, account: AccountContext) -> list[PositionItem]:
        """Return normalized domestic stock holdings for the account."""
        holdings = self._account_service.get_holding_stocks(account)
        return [
            PositionItem.from_holding_stock(holding) for holding in holdings if holding.quantity > 0
        ]
