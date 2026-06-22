"""Account summary formatting helpers."""

from __future__ import annotations

from decimal import Decimal


def format_currency(value: Decimal | None) -> str:
    """Format a currency amount for display."""
    if value is None:
        return "-"
    return f"{value:,.0f}"


def format_signed_currency(value: Decimal | None) -> str:
    """Format a signed currency amount for profit and loss display."""
    if value is None:
        return "-"
    formatted = format_currency(value)
    if value > 0:
        return f"+{formatted}"
    return formatted


def format_signed_percent(value: Decimal | None) -> str:
    """Format a signed percentage for profit and loss display."""
    if value is None:
        return "-"
    formatted = f"{value:.2f}%"
    if value > 0:
        return f"+{formatted}"
    return formatted
