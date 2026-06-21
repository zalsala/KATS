"""WebSocket TR ID registry for KIS OpenAPI."""

from __future__ import annotations

from typing import Final

WS_TR_REALTIME_PRICE: Final[str] = "H0STCNT0"
WS_TR_REALTIME_ORDERBOOK: Final[str] = "H0STASP0"
WS_TR_EXECUTION_NOTICE_MOCK: Final[str] = "H0STCNI0"
WS_TR_EXECUTION_NOTICE_REAL: Final[str] = "H0STCNI9"

TR_TYPE_SUBSCRIBE: Final[str] = "1"
TR_TYPE_UNSUBSCRIBE: Final[str] = "2"
