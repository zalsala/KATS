"""UiSession service binding tests."""

from __future__ import annotations

import pytest
from tests.fixtures.ui_fixtures import build_test_ui_session

pytestmark = pytest.mark.unit


def test_ui_session_starts_and_refreshes() -> None:
    session = build_test_ui_session()
    assert session.view_model.dashboard.summary is not None
    session.stop()
