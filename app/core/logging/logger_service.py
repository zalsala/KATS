"""Central logging service for KATS."""

from __future__ import annotations

import contextlib
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from app.config.config_models import LoggingConfig
from app.core.logging.constants import (
    CATEGORY_LOGGER_NAMES,
    DEFAULT_CATEGORY,
    LOG_CATEGORIES,
    LOG_ROOT_NAME,
    LogCategory,
)
from app.core.logging.handlers import create_category_handler, create_console_handler
from app.core.logging.performance import PerformanceLogger

logger = logging.getLogger(__name__)


class LoggerService:
    """Singleton service that configures and provides KATS loggers."""

    _instance: ClassVar[LoggerService | None] = None
    _init_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """Initialize an empty logger service."""
        self._configured = False
        self._logs_dir: Path | None = None
        self._config: LoggingConfig | None = None
        self._performance_loggers: dict[LogCategory, PerformanceLogger] = {}

    @classmethod
    def get_instance(cls) -> LoggerService:
        """Return the singleton ``LoggerService`` instance."""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton. Intended for testing only."""
        with cls._init_lock:
            if cls._instance is not None:
                cls._instance.shutdown()
            cls._instance = None

    @property
    def is_configured(self) -> bool:
        """Return True when logging has been configured."""
        return self._configured

    @property
    def logs_dir(self) -> Path | None:
        """Return the configured logs directory."""
        return self._logs_dir

    def setup(self, config: LoggingConfig, logs_dir: Path) -> None:
        """Configure the KATS logging system.

        Sets up console output, daily-rotating category file handlers,
        correlation ID injection, and sensitive data masking.

        Args:
            config: Logging configuration section.
            logs_dir: Directory where log files are stored.
        """
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._clear_handlers()

        root_level = getattr(logging, config.level)
        logging.getLogger().setLevel(root_level)

        kats_logger = logging.getLogger(LOG_ROOT_NAME)
        kats_logger.setLevel(root_level)
        kats_logger.propagate = False
        kats_logger.handlers.clear()

        if config.console_output:
            kats_logger.addHandler(create_console_handler(config))

        if config.file_output:
            for category in LOG_CATEGORIES:
                category_logger = logging.getLogger(CATEGORY_LOGGER_NAMES[category])
                category_logger.setLevel(root_level)
                category_logger.propagate = True
                category_logger.handlers.clear()
                category_logger.addHandler(create_category_handler(logs_dir, category, config))

        self._configured = True
        self._logs_dir = logs_dir
        self._config = config
        self._performance_loggers.clear()

        kats_logger.debug(
            "Logging initialized (level=%s, structured=%s, dir=%s)",
            config.level,
            config.structured,
            logs_dir,
        )

    def get_logger(
        self,
        name: str,
        category: LogCategory = DEFAULT_CATEGORY,
    ) -> logging.Logger:
        """Return a category-scoped logger under the ``kats`` namespace.

        Args:
            name: Logical module name appended to the category logger.
            category: Log category determining the output file.

        Returns:
            Configured ``logging.Logger`` instance.

        Raises:
            RuntimeError: If ``setup()`` has not been called yet.
        """
        if not self._configured:
            msg = "LoggerService.setup() must be called before get_logger()"
            raise RuntimeError(msg)

        base_name = CATEGORY_LOGGER_NAMES[category]
        full_name = f"{base_name}.{name}" if name else base_name
        return logging.getLogger(full_name)

    def get_performance_logger(
        self,
        category: LogCategory = LogCategory.API,
    ) -> PerformanceLogger:
        """Return a performance logger for the given category.

        Args:
            category: Log category used for latency records.

        Returns:
            ``PerformanceLogger`` bound to the category logger.
        """
        if category not in self._performance_loggers:
            self._performance_loggers[category] = PerformanceLogger(
                self.get_logger("performance", category=category)
            )
        return self._performance_loggers[category]

    def shutdown(self) -> None:
        """Flush and close all logging handlers."""
        for handler in logging.getLogger(LOG_ROOT_NAME).handlers:
            self._safe_close_handler(handler)

        for category in LOG_CATEGORIES:
            category_logger = logging.getLogger(CATEGORY_LOGGER_NAMES[category])
            for handler in category_logger.handlers:
                self._safe_close_handler(handler)
            category_logger.handlers.clear()

        logging.getLogger(LOG_ROOT_NAME).handlers.clear()
        self._configured = False
        self._performance_loggers.clear()

    @staticmethod
    def _safe_close_handler(handler: logging.Handler) -> None:
        """Flush and close a handler, ignoring already-closed streams."""
        with contextlib.suppress(ValueError):
            handler.flush()
        with contextlib.suppress(ValueError):
            handler.close()

    def cleanup_old_logs(self, *, max_age_days: int = 7) -> int:
        """Delete rotated log files older than the configured age.

        Returns:
            Number of deleted files.
        """
        if self._logs_dir is None or not self._logs_dir.is_dir():
            return 0
        if max_age_days <= 0:
            return 0

        cutoff_seconds = max_age_days * 24 * 60 * 60
        now = datetime.now(tz=UTC).timestamp()
        deleted = 0
        for path in self._logs_dir.glob("*.log*"):
            if not path.is_file():
                continue
            age_seconds = now - path.stat().st_mtime
            if age_seconds >= cutoff_seconds:
                path.unlink(missing_ok=True)
                deleted += 1
        return deleted

    @staticmethod
    def _clear_handlers() -> None:
        """Remove handlers from the root logger."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)


def setup_logging(config: LoggingConfig, logs_dir: Path) -> LoggerService:
    """Configure logging and return the ``LoggerService`` singleton.

    Args:
        config: Logging configuration section.
        logs_dir: Directory where log files are stored.

    Returns:
        Configured ``LoggerService`` instance.
    """
    service = LoggerService.get_instance()
    service.setup(config, logs_dir)
    return service


def get_logger(name: str, category: LogCategory = DEFAULT_CATEGORY) -> logging.Logger:
    """Return a logger from the ``LoggerService`` singleton.

    Args:
        name: Logical module name.
        category: Log category.

    Returns:
        Configured logger instance.
    """
    return LoggerService.get_instance().get_logger(name, category=category)
