class FinalertError(Exception):
    """Base exception for finalert."""


class ConfigurationError(FinalertError):
    """Raised when notification configuration is missing or invalid."""


class DeliveryError(FinalertError):
    """Raised when a provider rejects a notification."""
