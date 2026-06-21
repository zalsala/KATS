"""Log handler factory functions."""

from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config.config_models import LoggingConfig
from app.core.logging.constants import (
    DAILY_ROTATION_INTERVAL,
    DAILY_ROTATION_WHEN,
    LogCategory,
)
from app.core.logging.filters import CorrelationIdFilter, MinimumLevelFilter, SensitiveDataFilter
from app.core.logging.formatters import JsonLogFormatter, TextLogFormatter


def create_console_handler(config: LoggingConfig) -> logging.Handler:
    """Create a stdout console handler with text formatting.

    Args:
        config: Logging configuration.

    Returns:
        Configured stream handler.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(TextLogFormatter())
    handler.addFilter(CorrelationIdFilter())
    handler.addFilter(SensitiveDataFilter())
    handler.setLevel(getattr(logging, config.level))
    return handler


def create_file_handler(
    log_path: Path,
    config: LoggingConfig,
    *,
    min_level: int = logging.DEBUG,
) -> logging.Handler:
    """Create a daily-rotating file handler.

    Args:
        log_path: Target log file path.
        config: Logging configuration.
        min_level: Minimum log level for this handler.

    Returns:
        Configured timed rotating file handler.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if config.rotation:
        handler: logging.Handler = TimedRotatingFileHandler(
            filename=log_path,
            when=DAILY_ROTATION_WHEN,
            interval=DAILY_ROTATION_INTERVAL,
            backupCount=config.backup_count,
            encoding="utf-8",
            utc=False,
        )
    else:
        handler = logging.FileHandler(log_path, encoding="utf-8")

    formatter: logging.Formatter = JsonLogFormatter() if config.structured else TextLogFormatter()

    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())
    handler.addFilter(SensitiveDataFilter())
    handler.addFilter(MinimumLevelFilter(min_level))
    handler.setLevel(min_level)
    return handler


def create_category_handler(
    logs_dir: Path,
    category: LogCategory,
    config: LoggingConfig,
) -> logging.Handler:
    """Create a category-specific daily rotating file handler.

    Args:
        logs_dir: Root logs directory.
        category: Log category determining the file name.
        config: Logging configuration.

    Returns:
        Configured file handler for the category.
    """
    min_level = logging.ERROR if category == LogCategory.ERROR else logging.DEBUG
    log_path = logs_dir / f"{category.value}.log"
    return create_file_handler(log_path, config, min_level=min_level)
