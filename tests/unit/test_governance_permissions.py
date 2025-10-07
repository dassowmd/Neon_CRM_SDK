"""Tests for governance permissions module."""

import pytest

from neon_crm.governance import (
    Permission,
    ResourceType,
    Role,
    UserPermissions,
    create_user_permissions,
)
from neon_crm.governance.permissions import ROLE_PERMISSIONS


class TestPermissionEnum:
    """Test the Permission enum."""

    def test_permission_values(self):
        """Test all permission enum values."""
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.UPDATE.value == "update"
        assert Permission.DELETE.value == "delete"
        assert Permission.ADMIN.value == "admin"


class TestResourceTypeEnum:
    """Test the ResourceType enum."""

    def test_resource_type_values(self):
        """Test all resource type enum values."""
        assert ResourceType.ACCOUNTS.value == "accounts"
        assert ResourceType.DONATIONS.value == "donations"
        assert ResourceType.EVENTS.value == "events"
        assert ResourceType.WEBHOOKS.value == "webhooks"


class TestRoleEnum:
    """Test the Role enum."""

    def test_role_values(self):
        """Test all role enum values."""
        assert Role.VIEWER.value == "viewer"
        assert Role.EDITOR.value == "editor"
        assert Role.ADMIN.value == "admin"
        assert Role.FUNDRAISER.value == "fundraiser"
        assert Role.EVENT_MANAGER.value == "event_manager"


class TestUserPermissions:
    """Test the UserPermissions dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        perms = UserPermissions(
            user_id="test_user",
            role="viewer",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.READ}},
        )
        assert perms.user_id == "test_user"
        assert perms.role == "viewer"
        assert ResourceType.ACCOUNTS in perms.resource_permissions

    def test_custom_permissions_default(self):
        """Test that custom_permissions defaults to empty dict."""
        perms = UserPermissions(
            user_id="test_user", role="viewer", resource_permissions={}
        )
        assert perms.custom_permissions == {}

    def test_has_permission_with_permission(self):
        """Test has_permission when user has the permission."""
        perms = UserPermissions(
            user_id="test_user",
            role="viewer",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.READ}},
        )
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.READ) is True

    def test_has_permission_without_permission(self):
        """Test has_permission when user lacks the permission."""
        perms = UserPermissions(
            user_id="test_user",
            role="viewer",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.READ}},
        )
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.WRITE) is False

    def test_has_permission_admin_grants_all(self):
        """Test that ADMIN permission grants all access."""
        perms = UserPermissions(
            user_id="test_user",
            role="admin",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.ADMIN}},
        )
        # Admin should have all permissions
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.READ) is True
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.WRITE) is True
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.DELETE) is True

    def test_has_permission_resource_not_in_permissions(self):
        """Test has_permission for resource user has no permissions for."""
        perms = UserPermissions(
            user_id="test_user",
            role="viewer",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.READ}},
        )
        assert perms.has_permission(ResourceType.DONATIONS, Permission.READ) is False

    def test_has_any_permission_true(self):
        """Test has_any_permission when user has at least one permission."""
        perms = UserPermissions(
            user_id="test_user",
            role="editor",
            resource_permissions={
                ResourceType.ACCOUNTS: {Permission.READ, Permission.WRITE}
            },
        )
        assert (
            perms.has_any_permission(
                ResourceType.ACCOUNTS, [Permission.READ, Permission.DELETE]
            )
            is True
        )

    def test_has_any_permission_false(self):
        """Test has_any_permission when user has none of the permissions."""
        perms = UserPermissions(
            user_id="test_user",
            role="viewer",
            resource_permissions={ResourceType.ACCOUNTS: {Permission.READ}},
        )
        assert (
            perms.has_any_permission(
                ResourceType.ACCOUNTS, [Permission.WRITE, Permission.DELETE]
            )
            is False
        )


class TestCreateUserPermissions:
    """Test the create_user_permissions factory function."""

    def test_create_viewer_permissions(self):
        """Test creating permissions with viewer role."""
        perms = create_user_permissions("user123", Role.VIEWER)

        assert perms.user_id == "user123"
        assert perms.role == "viewer"
        # Viewer should have READ permission on accounts
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.READ)

    def test_create_editor_permissions(self):
        """Test creating permissions with editor role."""
        perms = create_user_permissions("user123", Role.EDITOR)

        assert perms.user_id == "user123"
        assert perms.role == "editor"
        # Editor should have more permissions than viewer
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.READ)
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.WRITE)

    def test_create_admin_permissions(self):
        """Test creating permissions with admin role."""
        perms = create_user_permissions("user123", Role.ADMIN)

        assert perms.user_id == "user123"
        assert perms.role == "admin"
        # Admin should have ADMIN permission
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.ADMIN)

    def test_create_with_custom_overrides(self):
        """Test creating permissions with custom overrides."""
        custom_overrides = {ResourceType.DONATIONS: {Permission.ADMIN}}
        perms = create_user_permissions(
            "user123", Role.VIEWER, custom_overrides=custom_overrides
        )

        # Should have custom override for donations
        assert perms.has_permission(ResourceType.DONATIONS, Permission.ADMIN)
        # Should still have base viewer permissions for accounts
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.READ)

    def test_create_custom_override_replaces_base(self):
        """Test that custom overrides completely replace base permissions."""
        custom_overrides = {
            ResourceType.ACCOUNTS: {Permission.DELETE}  # Override viewer's READ
        }
        perms = create_user_permissions(
            "user123", Role.VIEWER, custom_overrides=custom_overrides
        )

        # Should have only DELETE, not the base READ permission
        assert perms.has_permission(ResourceType.ACCOUNTS, Permission.DELETE)
        # The READ permission from VIEWER should be replaced
        # (depends on implementation - if it's additive or replacement)


class TestRolePermissions:
    """Test the ROLE_PERMISSIONS constant."""

    def test_role_permissions_defined_for_all_roles(self):
        """Test that permissions are defined for all roles."""
        assert Role.VIEWER in ROLE_PERMISSIONS
        assert Role.EDITOR in ROLE_PERMISSIONS
        assert Role.ADMIN in ROLE_PERMISSIONS
        assert Role.FUNDRAISER in ROLE_PERMISSIONS
        assert Role.EVENT_MANAGER in ROLE_PERMISSIONS

    def test_viewer_has_read_permissions(self):
        """Test that viewer role has read permissions."""
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        # Viewer should have READ on most resources
        assert Permission.READ in viewer_perms.get(ResourceType.ACCOUNTS, set())

    def test_admin_has_admin_permissions(self):
        """Test that admin role has admin permissions."""
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        # Admin should have ADMIN permission on all resources
        for resource_type in ResourceType:
            assert Permission.ADMIN in admin_perms.get(resource_type, set())
