"""Account domain exceptions."""


class AccountDomainError(Exception):
    """Base exception for account domain errors."""


class InvalidAccountContextError(AccountDomainError):
    """Raised when account number or product code is invalid."""
