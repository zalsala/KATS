"""Strategy control tests."""

from __future__ import annotations

import pytest
from tests.fixtures.ui_fixtures import build_test_ui_controller

pytestmark = pytest.mark.unit


def test_strategy_register_start_stop() -> None:
    controller = build_test_ui_controller()
    dto = controller.register_strategy(
        strategy_type="template",
        name="ui-test",
        symbols=["005930"],
    )
    assert dto.strategy_id
    started = controller.start_strategy(dto.strategy_id)
    assert started.state == "running"
    stopped = controller.stop_strategy(dto.strategy_id)
    assert stopped.state == "stopped"
