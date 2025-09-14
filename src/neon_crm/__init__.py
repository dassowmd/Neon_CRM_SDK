"""Neon CRM Python SDK

A comprehensive Python SDK for the Neon CRM API v2.
"""

__version__ = "0.1.0"

from .client import NeonClient
from .exceptions import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonError,
    NeonNotFoundError,
    NeonRateLimitError,
)
from .types import UserType

__all__ = [
    "__version__",
    "NeonClient",
    "UserType",
    "NeonError",
    "NeonAPIError",
    "NeonAuthenticationError",
    "NeonNotFoundError",
    "NeonRateLimitError",
]
