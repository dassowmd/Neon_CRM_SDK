"""Example of using the governance system with the Neon CRM SDK.

This example demonstrates both the simplified role-based approach (recommended)
and the advanced permission configuration approach.
"""

import os
from neon_crm import NeonClient
from neon_crm.governance import (
    Role,
    Permission,
    ResourceType,
    PermissionConfig,
    PermissionError,
)


def example_simple_role():
    """Simplest way to use governance - just specify a role."""
    print("=== Simple Role-Based Usage (RECOMMENDED) ===")

    # Create a client with a fundraiser role
    # Governance is enabled by default
    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        default_role="fundraiser",  # Can also use Role.FUNDRAISER
    )

    try:
        # This will work - fundraisers can read accounts
        accounts = list(client.accounts.list(page_size=5))
        print(f"✓ Successfully retrieved {len(accounts)} accounts")

        # This will work - fundraisers can create donations
        # donation_data = {...}
        # client.donations.create(donation_data)

    except PermissionError as e:
        print(f"✗ Permission denied: {e}")


def example_role_with_overrides():
    """Use a role but override permissions for specific resources."""
    print("\n=== Role with Permission Overrides ===")

    # Start with viewer role (read-only) but allow creating donations
    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        default_role="viewer",
        permission_overrides={
            "donations": {"read", "write"},  # Can use strings
            ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE},  # Or enums
        },
    )

    try:
        # This will work - viewers can read
        accounts = list(client.accounts.list(page_size=2))
        print(f"✓ Read {len(accounts)} accounts (viewer permission)")

        # This will work - we overrode to allow donation writes
        # donation_data = {...}
        # client.donations.create(donation_data)
        print("✓ Can create donations (permission override)")

        # This will fail - viewers can't create accounts (no override)
        # client.accounts.create({...})

    except PermissionError as e:
        print(f"✗ Permission denied: {e}")


def example_env_variables():
    """Use environment variables for configuration."""
    print("\n=== Using Environment Variables ===")

    # Set these in your .env file or environment:
    # NEON_DEFAULT_ROLE=editor

    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        # Role loaded from NEON_DEFAULT_ROLE environment variable
    )

    print(f"Governance enabled: {client.governance_enabled}")
    if client.user_permissions:
        print(f"Role: {client.user_permissions.role}")
    else:
        print("Using default 'viewer' role")


def example_switching_roles():
    """Advanced: Dynamically switching roles on the same client."""
    print("\n=== Advanced: Switching Roles ===")

    # Create a client with admin role
    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        default_role="admin",
    )

    try:
        # Admin can do anything
        accounts = list(client.accounts.list(page_size=2))
        print(f"✓ Admin accessed {len(accounts)} accounts")
    except PermissionError as e:
        print(f"✗ Admin permission denied: {e}")

    # Change to viewer role for read-only operations
    viewer_client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        default_role="viewer",
    )

    try:
        # Viewer can read
        accounts = list(viewer_client.accounts.list(page_size=2))
        print(f"✓ Viewer accessed {len(accounts)} accounts")

        # But viewer cannot create (this would fail)
        # viewer_client.accounts.create({...})  # Would raise PermissionError

    except PermissionError as e:
        print(f"✗ Viewer permission denied: {e}")


def example_advanced_permission_config():
    """Advanced: Using PermissionConfig for multi-user scenarios."""
    print("\n=== Advanced: Permission Configuration ===")

    # Create a permission configuration
    config = PermissionConfig()

    # Add users to the configuration
    config.add_user("fundraiser1", Role.FUNDRAISER)
    config.add_user("admin1", Role.ADMIN)
    config.add_user("event_manager1", Role.EVENT_MANAGER)

    # Create a client with the configuration
    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        permission_config=config,
    )

    # Set user by ID (looks up in configuration)
    if client.set_user_by_id("fundraiser1"):
        print("✓ Successfully set user permissions from config")

        # Get current user's permissions for donations
        perms = config.get_effective_permissions("fundraiser1", ResourceType.DONATIONS)
        print(f"  Fundraiser1 donation permissions: {[p.value for p in perms]}")
    else:
        print("✗ User not found in configuration")

    # List all users with donation write permission
    users_with_write = config.list_users_with_permission(
        ResourceType.DONATIONS, Permission.WRITE
    )
    print(f"  Users who can create donations: {users_with_write}")


def example_available_roles():
    """Show available roles and their permissions."""
    print("\n=== Available Roles ===")

    roles_info = {
        "viewer": "Read-only access to most resources",
        "editor": "Read and write access to most resources",
        "admin": "Full access to all resources",
        "fundraiser": "Focused on donation and fundraising activities",
        "event_manager": "Focused on event management",
        "volunteer_coordinator": "Focused on volunteer management",
    }

    for role, description in roles_info.items():
        print(f"  • {role}: {description}")


def main():
    """Run all governance examples."""
    print("Neon CRM SDK Governance Examples")
    print("=" * 50)
    print("\nThese examples show both simple and advanced usage.")
    print("For most use cases, the simple role-based approach is recommended.\n")

    try:
        # Simple examples (recommended for most users)
        example_available_roles()
        example_simple_role()
        example_role_with_overrides()
        example_env_variables()

        # Advanced examples (for complex scenarios)
        example_switching_roles()
        example_advanced_permission_config()

    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        print("Make sure to set NEON_ORG_ID and NEON_API_KEY environment variables")


if __name__ == "__main__":
    main()
