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
    NeonUnsupportedMediaTypeError,
)
from .types import CustomFieldCategory, SearchOperator, UserType
from .validation import SearchRequestValidator, validate_search_request
from .custom_field_types import CustomFieldTypeMapper
from .governance import Permission, Role

__all__ = [
    "__version__",
    "NeonClient",
    "UserType",
    "CustomFieldCategory",
    "SearchOperator",
    "SearchRequestValidator",
    "validate_search_request",
    "CustomFieldTypeMapper",
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
    "NeonUnsupportedMediaTypeError",
    "Permission",
    "Role",
]
