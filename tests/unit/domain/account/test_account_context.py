"""Unit tests for AccountContext."""

from __future__ import annotations

import pytest

from app.domain.account.exceptions import InvalidAccountContextError
from app.domain.account.value_objects.account_context import AccountContext

pytestmark = pytest.mark.unit


class TestAccountContext:
    """Tests for AccountContext."""

    def test_valid_context(self) -> None:
        account = AccountContext(account_no="12345678", account_product="01")

        assert account.to_base_params() == {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_invalid_account_no(self) -> None:
        with pytest.raises(InvalidAccountContextError):
            AccountContext(account_no="1234")
