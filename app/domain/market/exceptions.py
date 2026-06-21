"""Market domain exceptions."""


class MarketDomainError(Exception):
    """Base exception for market domain errors."""


class InvalidSymbolError(MarketDomainError):
    """Raised when a stock symbol format is invalid."""
