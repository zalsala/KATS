"""Unit tests for AuthenticationClient."""

from __future__ import annotations

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport

from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.exceptions import (
    ApprovalKeyError,
    HashKeyError,
    InvalidCredentialError,
    TokenRefreshError,
)

pytestmark = pytest.mark.unit


class TestAuthenticationClient:
    """Tests for AuthenticationClient."""

    def test_issue_access_token_success(self) -> None:
        """issue_access_token parses official response fields."""
        transport = MockHttpTransport()
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )

        token = client.issue_access_token("app-key", "app-secret")

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1
        call_url, _, body = transport.calls[0]
        assert call_url.endswith("/oauth2/tokenP")
        assert body["grant_type"] == "client_credentials"
        assert body["appkey"] == "app-key"
        assert body["appsecret"] == "app-secret"

    def test_issue_access_token_missing_credentials(self) -> None:
        """Missing credentials raise InvalidCredentialError."""
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=MockHttpTransport(),
        )

        with pytest.raises(InvalidCredentialError):
            client.issue_access_token("", "secret")

    def test_issue_access_token_http_error(self) -> None:
        """Non-200 token response raises TokenRefreshError."""
        transport = MockHttpTransport(status_code=401)
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )

        with pytest.raises(TokenRefreshError):
            client.issue_access_token("app-key", "app-secret")

    def test_issue_approval_key_success(self) -> None:
        """issue_approval_key uses secretkey field per official API."""
        transport = MockHttpTransport()
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )

        approval = client.issue_approval_key(
            "app-key",
            "app-secret",
            access_token="rest-token",
        )

        assert approval.key == "mock-approval-key"
        _, _, body = transport.calls[0]
        assert body["secretkey"] == "app-secret"
        assert body["token"] == "rest-token"

    def test_issue_approval_key_http_error(self) -> None:
        """Non-200 approval response raises ApprovalKeyError."""
        transport = MockHttpTransport(status_code=500)
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )

        with pytest.raises(ApprovalKeyError):
            client.issue_approval_key("app-key", "app-secret")

    def test_issue_hash_key_success(self) -> None:
        """issue_hash_key returns HASH field from response."""
        transport = MockHttpTransport()
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )
        headers = {"authorization": "Bearer token", "appkey": "key", "appsecret": "secret"}

        hash_value = client.issue_hash_key(headers, {"ORD_QTY": "1"})

        assert hash_value == "mock-hash-key"
        call_url, _, _ = transport.calls[0]
        assert call_url.endswith("/uapi/hashkey")

    def test_issue_hash_key_http_error(self) -> None:
        """Non-200 hashkey response raises HashKeyError."""
        transport = MockHttpTransport(status_code=403)
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )

        with pytest.raises(HashKeyError):
            client.issue_hash_key({}, {})
