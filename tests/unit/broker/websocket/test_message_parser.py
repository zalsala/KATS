"""MessageParser tests."""

from __future__ import annotations

import pytest
from tests.fixtures.ws_fixtures import (
    sample_execution_pipe_message,
    sample_orderbook_pipe_message,
    sample_price_pipe_message,
)

from app.broker.kis.websocket.exceptions import WebSocketParseError
from app.broker.kis.websocket.message_parser import MessageParser

pytestmark = pytest.mark.unit


class TestMessageParser:
    """Tests for KIS WebSocket MessageParser."""

    def test_parse_realtime_price(self) -> None:
        parser = MessageParser()

        message = parser.parse(sample_price_pipe_message())

        assert message is not None
        assert message.symbol_code == "005930"
        assert message.price == "70000"

    def test_parse_realtime_orderbook(self) -> None:
        parser = MessageParser()

        message = parser.parse(sample_orderbook_pipe_message())

        assert message is not None
        assert message.ask_price_1 == "70100"
        assert message.bid_price_1 == "70000"

    def test_parse_execution_notice(self) -> None:
        parser = MessageParser()

        message = parser.parse(sample_execution_pipe_message())

        assert message is not None
        assert message.order_number == "0000123456"
        assert message.executed_price == "70000"

    def test_parse_ping_returns_none(self) -> None:
        parser = MessageParser()

        assert parser.parse("PINGPONG") is None

    def test_parse_invalid_raises(self) -> None:
        parser = MessageParser()

        with pytest.raises(WebSocketParseError):
            parser.parse("invalid-message")
