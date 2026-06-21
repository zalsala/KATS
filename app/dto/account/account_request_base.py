"""Account request helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.account.value_objects.account_context import AccountContext


class AccountRequestBase(BaseModel):
    """Base request fields for account APIs."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    account: AccountContext

    def base_params(self) -> dict[str, str]:
        """Return CANO and ACNT_PRDT_CD parameters."""
        return self.account.to_base_params()
