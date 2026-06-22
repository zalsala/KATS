"""KIS domestic account summary adapter."""

from __future__ import annotations

from app.domain.account.account_summary import AccountSummary
from app.domain.account.value_objects.account_context import AccountContext
from app.service.account.account_service import AccountService


class KISDomesticAccountSummaryAdapter:
    """Adapter for KIS domestic stock account summary inquiry."""

    def __init__(self, *, account_service: AccountService) -> None:
        self._account_service = account_service

    def get_account_summary(self, account: AccountContext) -> AccountSummary:
        """Return normalized account summary from balance inquiry."""
        deposit, balance = self._account_service.get_balance_summary(account)
        return AccountSummary.from_balance_and_deposit(balance=balance, deposit=deposit)
