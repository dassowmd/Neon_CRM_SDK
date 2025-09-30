"""Access control decorators and context management."""

import functools
from typing import TYPE_CHECKING, Any, Callable, Optional
from contextvars import ContextVar

from ..exceptions import NeonAPIError
from .permissions import Permission, ResourceType, UserPermissions

if TYPE_CHECKING:
    from typing import TypeVar, ParamSpec

    P = ParamSpec("P")
    T = TypeVar("T")

# Context variable to store current user permissions
_current_permissions: ContextVar[Optional[UserPermissions]] = ContextVar(
    "current_permissions", default=None
)


class PermissionError(NeonAPIError):
    """Raised when a user lacks required permissions."""

    def __init__(
        self,
        message: str,
        resource: ResourceType,
        permission: Permission,
        user_id: str = None,
    ):
        super().__init__(message, status_code=403)
        self.resource = resource
        self.permission = permission
        self.user_id = user_id


class PermissionContext:
    """Context manager for setting user permissions during API calls."""

    def __init__(self, permissions: UserPermissions):
        self.permissions = permissions
        self.token = None

    def __enter__(self):
        self.token = _current_permissions.set(self.permissions)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _current_permissions.reset(self.token)

    @classmethod
    def get_current_permissions(cls) -> Optional[UserPermissions]:
        """Get the current user permissions from context."""
        return _current_permissions.get()

    @classmethod
    def require_current_permissions(cls) -> UserPermissions:
        """Get current permissions or raise an error if none are set."""
        permissions = cls.get_current_permissions()
        if permissions is None:
            raise PermissionError(
                "No user permissions set. Use PermissionContext or set permissions on client.",
                resource=ResourceType.ACCOUNTS,  # Default resource for generic errors
                permission=Permission.READ,
            )
        return permissions


def requires_permission(resource: ResourceType, permission: Permission):
    """Decorator to enforce permission requirements on methods.

    Args:
        resource: The resource type being accessed
        permission: The required permission level

    Raises:
        PermissionError: If the user lacks the required permission
    """

    def decorator(func: "Callable[P, T]") -> "Callable[P, T]":
        @functools.wraps(func)
        def wrapper(*args: "P.args", **kwargs: "P.kwargs") -> "T":
            # Get current user permissions
            permissions = PermissionContext.get_current_permissions()

            if permissions is None:
                raise PermissionError(
                    f"Authentication required to access {resource.value}",
                    resource=resource,
                    permission=permission,
                )

            # Check if user has the required permission
            if not permissions.has_permission(resource, permission):
                raise PermissionError(
                    f"User '{permissions.user_id}' lacks '{permission.value}' permission for '{resource.value}'",
                    resource=resource,
                    permission=permission,
                    user_id=permissions.user_id,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def requires_any_permission(resource: ResourceType, permissions: list[Permission]):
    """Decorator to enforce that user has at least one of the specified permissions.

    Args:
        resource: The resource type being accessed
        permissions: List of acceptable permissions (user needs at least one)

    Raises:
        PermissionError: If the user lacks all required permissions
    """

    def decorator(func: "Callable[P, T]") -> "Callable[P, T]":
        @functools.wraps(func)
        def wrapper(*args: "P.args", **kwargs: "P.kwargs") -> "T":
            user_permissions = PermissionContext.get_current_permissions()

            if user_permissions is None:
                raise PermissionError(
                    f"Authentication required to access {resource.value}",
                    resource=resource,
                    permission=permissions[
                        0
                    ],  # Use first permission for error reporting
                )

            # Check if user has any of the required permissions
            if not user_permissions.has_any_permission(resource, permissions):
                perm_names = [p.value for p in permissions]
                raise PermissionError(
                    f"User '{user_permissions.user_id}' lacks required permissions for '{resource.value}'. "
                    f"Needs one of: {', '.join(perm_names)}",
                    resource=resource,
                    permission=permissions[0],
                    user_id=user_permissions.user_id,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_permission(resource: ResourceType, permission: Permission) -> bool:
    """Check if the current user has a specific permission.

    Args:
        resource: The resource type
        permission: The permission to check

    Returns:
        True if user has permission, False otherwise
    """
    permissions = PermissionContext.get_current_permissions()
    if permissions is None:
        return False

    return permissions.has_permission(resource, permission)


def get_user_permissions_for_resource(resource: ResourceType) -> set[Permission]:
    """Get all permissions the current user has for a specific resource.

    Args:
        resource: The resource type

    Returns:
        Set of permissions the user has for this resource
    """
    permissions = PermissionContext.get_current_permissions()
    if permissions is None:
        return set()

    return permissions.resource_permissions.get(resource, set())


class PermissionChecker:
    """Helper class for checking permissions in resource methods."""

    @staticmethod
    def ensure_permission(
        resource: ResourceType, permission: Permission, custom_message: str = None
    ):
        """Ensure current user has required permission, raise error if not.

        Args:
            resource: The resource type
            permission: Required permission
            custom_message: Custom error message (optional)

        Raises:
            PermissionError: If permission is not granted
        """
        permissions = PermissionContext.get_current_permissions()

        if permissions is None:
            message = (
                custom_message or f"Authentication required to access {resource.value}"
            )
            raise PermissionError(message, resource=resource, permission=permission)

        if not permissions.has_permission(resource, permission):
            message = (
                custom_message
                or f"User '{permissions.user_id}' lacks '{permission.value}' permission for '{resource.value}'"
            )
            raise PermissionError(
                message,
                resource=resource,
                permission=permission,
                user_id=permissions.user_id,
            )

    @staticmethod
    def ensure_any_permission(
        resource: ResourceType,
        permissions_list: list[Permission],
        custom_message: str = None,
    ):
        """Ensure current user has at least one of the required permissions.

        Args:
            resource: The resource type
            permissions_list: List of acceptable permissions
            custom_message: Custom error message (optional)

        Raises:
            PermissionError: If no required permission is granted
        """
        permissions = PermissionContext.get_current_permissions()

        if permissions is None:
            message = (
                custom_message or f"Authentication required to access {resource.value}"
            )
            raise PermissionError(
                message, resource=resource, permission=permissions_list[0]
            )

        if not permissions.has_any_permission(resource, permissions_list):
            perm_names = [p.value for p in permissions_list]
            message = (
                custom_message
                or f"User '{permissions.user_id}' lacks required permissions for '{resource.value}'. "
                f"Needs one of: {', '.join(perm_names)}"
            )
            raise PermissionError(
                message,
                resource=resource,
                permission=permissions_list[0],
                user_id=permissions.user_id,
            )
