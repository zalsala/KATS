"""Trading application service with environment safeguards."""

from __future__ import annotations

import logging
import re

from app.account.kis_domestic_account_summary_adapter import KISDomesticAccountSummaryAdapter
from app.account.kis_domestic_balance_adapter import KISDomesticBalanceAdapter
from app.config.config_manager import ConfigManager
from app.domain.account.account_summary import AccountSummary
from app.domain.account.value_objects.account_context import AccountContext
from app.domain.order.order_result import OrderResult
from app.domain.position.position_item import PositionItem
from app.dto.order.order_entry_request import OrderEntryRequest
from app.order.kis_domestic_order_adapter import KISDomesticOrderAdapter
from app.service.order.order_service import OrderService, OrderValidationError

logger = logging.getLogger(__name__)

SYMBOL_PATTERN = re.compile(r"^\d{6}$")


class TradingNotAllowedError(Exception):
    """Raised when order placement is blocked by configuration or environment."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TradingService:
    """Validate and route domestic stock cash orders through the KIS adapter."""

    def __init__(
        self,
        *,
        order_service: OrderService | None,
        config_manager: ConfigManager,
        adapter: KISDomesticOrderAdapter | None = None,
        balance_adapter: KISDomesticBalanceAdapter | None = None,
        account_summary_adapter: KISDomesticAccountSummaryAdapter | None = None,
    ) -> None:
        self._order_service = order_service
        self._config_manager = config_manager
        self._adapter = adapter
        self._balance_adapter = balance_adapter
        self._account_summary_adapter = account_summary_adapter

    def is_trading_available(self) -> bool:
        """Return True when order placement is allowed for the current environment."""
        try:
            self._ensure_trading_allowed()
        except TradingNotAllowedError:
            return False
        return True

    def trading_status_message(self) -> str:
        """Return a user-facing trading availability message."""
        if self._order_service is None or self._adapter is None:
            return "Order service is not configured"
        settings = self._config_manager.load()
        secrets = settings.secrets
        if not secrets.is_configured:
            return "Trading credentials are not configured"
        if not secrets.account_no:
            return "Account number is not configured"
        if secrets.is_real and not settings.config.order.live_trading_enabled:
            return "Real trading is disabled in configuration"
        if secrets.is_real:
            return "Real trading enabled"
        return "VTS mock trading enabled"

    def is_position_lookup_available(self) -> bool:
        """Return True when holdings lookup is allowed for the current environment."""
        try:
            self._ensure_lookup_allowed()
        except TradingNotAllowedError:
            return False
        return True

    def position_lookup_status_message(self) -> str:
        """Return a user-facing position lookup availability message."""
        if self._balance_adapter is None:
            return "Account service is not configured"
        settings = self._config_manager.load()
        secrets = settings.secrets
        if not secrets.is_configured:
            return "Trading credentials are not configured"
        if not secrets.account_no:
            return "Account number is not configured"
        if secrets.is_real and not settings.config.order.live_trading_enabled:
            return "Real account lookup is disabled in configuration"
        if secrets.is_real:
            return "Real account lookup enabled"
        return "VTS mock account lookup enabled"

    def get_positions(self) -> list[PositionItem]:
        """Return normalized domestic stock holdings for the active account."""
        self._ensure_lookup_allowed()
        account = self._resolve_account_context()
        assert self._balance_adapter is not None
        logger.info(
            "Fetching %s domestic stock positions",
            "mock" if self._is_mock_trading() else "live",
        )
        return self._balance_adapter.get_positions(account)

    def is_account_summary_available(self) -> bool:
        """Return True when account summary lookup is allowed."""
        return self.is_position_lookup_available()

    def account_summary_status_message(self) -> str:
        """Return a user-facing account summary availability message."""
        if self._account_summary_adapter is None:
            return "Account service is not configured"
        return self.position_lookup_status_message()

    def get_account_summary(self) -> AccountSummary:
        """Return normalized domestic stock account summary."""
        self._ensure_account_summary_allowed()
        account = self._resolve_account_context()
        assert self._account_summary_adapter is not None
        logger.info(
            "Fetching %s domestic stock account summary",
            "mock" if self._is_mock_trading() else "live",
        )
        return self._account_summary_adapter.get_account_summary(account)

    def validate(self, request: OrderEntryRequest) -> list[str]:
        """Validate an order entry request before submission."""
        errors: list[str] = []
        symbol = request.symbol_code.strip()
        if not SYMBOL_PATTERN.match(symbol):
            errors.append("Symbol must be a 6-digit stock code")
        if request.side not in {"buy", "sell"}:
            errors.append("Side must be buy or sell")
        if request.order_type not in {"limit", "market"}:
            errors.append("Order type must be limit or market")
        if not request.quantity.isdigit() or int(request.quantity) <= 0:
            errors.append("Quantity must be a positive integer")
        if request.order_type == "market":
            if request.price != "0":
                errors.append("Market order price must be 0")
        elif not request.price.isdigit() or int(request.price) <= 0:
            errors.append("Limit price must be a positive integer")
        return errors

    def place_order(self, request: OrderEntryRequest) -> OrderResult:
        """Place a validated domestic stock cash order."""
        self._ensure_trading_allowed()
        errors = self.validate(request)
        if errors:
            raise OrderValidationError(errors[0])

        account = self._resolve_account_context()
        assert self._adapter is not None
        logger.info(
            "Placing %s %s order symbol=%s type=%s qty=%s",
            "mock" if self._is_mock_trading() else "live",
            request.side,
            request.symbol_code,
            request.order_type,
            request.quantity,
        )
        return self._adapter.place_order(request, account=account)

    def _ensure_trading_allowed(self) -> None:
        if self._order_service is None or self._adapter is None:
            raise TradingNotAllowedError("Order service is not configured")

        settings = self._config_manager.load()
        secrets = settings.secrets
        if not secrets.is_configured:
            raise TradingNotAllowedError("Trading credentials are not configured")
        if not secrets.account_no:
            raise TradingNotAllowedError("Account number is not configured")

        if secrets.is_real and not settings.config.order.live_trading_enabled:
            raise TradingNotAllowedError(
                "Real trading is disabled. Enable order.live_trading_enabled to proceed.",
            )

    def _ensure_account_summary_allowed(self) -> None:
        if self._account_summary_adapter is None:
            raise TradingNotAllowedError("Account service is not configured")
        self._ensure_account_access_allowed()

    def _ensure_lookup_allowed(self) -> None:
        if self._balance_adapter is None:
            raise TradingNotAllowedError("Account service is not configured")
        self._ensure_account_access_allowed()

    def _ensure_account_access_allowed(self) -> None:
        settings = self._config_manager.load()
        secrets = settings.secrets
        if not secrets.is_configured:
            raise TradingNotAllowedError("Trading credentials are not configured")
        if not secrets.account_no:
            raise TradingNotAllowedError("Account number is not configured")

        if secrets.is_real and not settings.config.order.live_trading_enabled:
            raise TradingNotAllowedError(
                "Real account lookup is disabled. Enable order.live_trading_enabled to proceed.",
            )

    def _resolve_account_context(self) -> AccountContext:
        settings = self._config_manager.load()
        account_no = settings.secrets.account_no
        if not account_no:
            raise TradingNotAllowedError("Account number is not configured")
        return AccountContext(account_no=account_no, account_product="01")

    def _is_mock_trading(self) -> bool:
        settings = self._config_manager.load()
        return settings.secrets.is_mock
