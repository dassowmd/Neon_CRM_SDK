"""Neon CRM Python SDK

A comprehensive Python SDK for the Neon CRM API v2.
"""

__version__ = "0.1.0"

from .client import NeonClient
from .exceptions import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonBadRequestError,
    NeonConflictError,
    NeonError,
    NeonForbiddenError,
    NeonNotFoundError,
    NeonRateLimitError,
    NeonServerError,
    NeonUnprocessableEntityError,
)
from .types import UserType

__all__ = [
    "__version__",
    "NeonClient",
    "UserType",
    "NeonError",
    "NeonAPIError",
    "NeonAuthenticationError",
    "NeonBadRequestError",
    "NeonConflictError",
    "NeonForbiddenError",
    "NeonNotFoundError",
    "NeonRateLimitError",
    "NeonServerError",
    "NeonUnprocessableEntityError",
]
