"""Custom exceptions for Bootstrap."""


class BootstrapError(Exception):
    """Base exception for all Bootstrap errors."""
    pass


class PlatformError(BootstrapError):
    """Platform-specific error."""
    pass


class PackageError(BootstrapError):
    """Package installation error."""
    pass


class PrivilegeError(BootstrapError):
    """Privilege escalation error."""
    pass


class ConfigError(BootstrapError):
    """Configuration error."""
    pass


class DetectionError(BootstrapError):
    """System detection error."""
    pass


class ShellError(BootstrapError):
    """Shell setup error."""
    pass


class ValidationError(BootstrapError):
    """Validation error."""
    pass
