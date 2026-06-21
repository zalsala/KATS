"""Configuration layer exceptions."""


class ConfigError(Exception):
    """Base exception for configuration errors."""


class ConfigLoadError(ConfigError):
    """Raised when configuration files cannot be loaded."""


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""


class ConfigSaveError(ConfigError):
    """Raised when user settings cannot be saved."""


class SecretValidationError(ConfigError):
    """Raised when required secrets are missing or invalid."""
