"""KIS API framework enumerations."""

from __future__ import annotations

from enum import StrEnum


class ApiCategory(StrEnum):
    """Official KIS OpenAPI category aligned with GitHub ``examples_user/`` folders."""

    AUTH = "auth"
    DOMESTIC_STOCK = "domestic_stock"
    OVERSEAS_STOCK = "overseas_stock"
    DOMESTIC_BOND = "domestic_bond"
    DOMESTIC_FUTUREOPTION = "domestic_futureoption"
    OVERSEAS_FUTUREOPTION = "overseas_futureoption"
    ELW = "elw"
    ETFETN = "etfetn"


class HttpMethod(StrEnum):
    """Supported HTTP methods for KIS REST APIs."""

    GET = "GET"
    POST = "POST"
