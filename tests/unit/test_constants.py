"""Unit tests for application constants."""

from __future__ import annotations

import pytest

from app.core.constants import (
    APP_NAME,
    ENV_KIS_APP_KEY,
    KIS_REAL_REST_BASE_URL,
    KIS_VTS_REST_BASE_URL,
    SECRET_ENV_KEYS,
    SUPPORTED_ENVIRONMENTS,
)

pytestmark = pytest.mark.unit


class TestConstants:
    """Tests for application constants."""

    def test_app_name(self) -> None:
        """APP_NAME is KATS."""
        assert APP_NAME == "KATS"

    def test_supported_environments(self) -> None:
        """All expected environments are supported."""
        assert "development" in SUPPORTED_ENVIRONMENTS
        assert "simulation" in SUPPORTED_ENVIRONMENTS
        assert "production" in SUPPORTED_ENVIRONMENTS

    def test_kis_rest_urls_are_distinct(self) -> None:
        """VTS and real KIS REST URLs are different."""
        assert KIS_VTS_REST_BASE_URL != KIS_REAL_REST_BASE_URL

    def test_kis_ws_urls_match_official(self) -> None:
        """VTS and real WebSocket URLs match kis_devlp.yaml (vops vs ops)."""
        from app.core.constants import KIS_REAL_WS_URL, KIS_VTS_WS_URL

        assert ":31000" in KIS_VTS_WS_URL
        assert ":21000" in KIS_REAL_WS_URL
        assert KIS_VTS_WS_URL != KIS_REAL_WS_URL

    def test_secret_env_keys_contains_app_key(self) -> None:
        """SECRET_ENV_KEYS includes KIS_APP_KEY."""
        assert ENV_KIS_APP_KEY in SECRET_ENV_KEYS
