from finalert.core import notify, watch
from finalert.exceptions import ConfigurationError, DeliveryError, FinalertError

__all__ = [
    "ConfigurationError",
    "DeliveryError",
    "FinalertError",
    "notify",
    "watch",
]
__version__ = "0.2.0"
