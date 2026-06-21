"""Authentication-related broker exceptions."""

from __future__ import annotations


class BrokerError(Exception):
    """Base exception for broker layer errors."""


class AuthenticationError(BrokerError):
    """Raised when authentication fails."""


class TokenExpiredError(AuthenticationError):
    """Raised when an access token has expired."""


class TokenRefreshError(AuthenticationError):
    """Raised when access token refresh fails."""


class ApprovalKeyError(AuthenticationError):
    """Raised when WebSocket approval key issuance fails."""


class HashKeyError(AuthenticationError):
    """Raised when hash key generation fails."""


class InvalidCredentialError(AuthenticationError):
    """Raised when KIS API credentials are missing or invalid."""
