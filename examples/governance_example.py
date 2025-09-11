"""Example of using the governance system with the Neon CRM SDK."""

import os
from neon_crm import NeonClient
from neon_crm.governance import (
    Role, 
    Permission, 
    ResourceType, 
    create_user_permissions,
    PermissionConfig,
    PermissionContext,
    PermissionError
)

# Initialize the client with API credentials
client = NeonClient(
    org_id=os.getenv("NEON_ORG_ID"),
    api_key=os.getenv("NEON_API_KEY")
)

def example_basic_usage():
    """Basic usage of the governance system."""
    print("=== Basic Governance Usage ===")
    
    # Create a user with fundraiser role
    fundraiser_permissions = create_user_permissions("user123", Role.FUNDRAISER)
    
    # Set the user permissions on the client
    client.set_user_permissions(fundraiser_permissions)
    
    try:
        # This will work - fundraisers can read accounts
        accounts = list(client.accounts.list(page_size=5))
        print(f"Successfully retrieved {len(accounts)} accounts")
        
        # This will work - fundraisers can create donations
        # donation_data = {...}
        # client.donations.create(donation_data)
        
    except PermissionError as e:
        print(f"Permission denied: {e}")


def example_with_context_manager():
    """Using permission contexts for temporary access."""
    print("\n=== Context Manager Usage ===")
    
    # Create different permission levels
    admin_permissions = create_user_permissions("admin_user", Role.ADMIN)
    viewer_permissions = create_user_permissions("viewer_user", Role.VIEWER)
    
    # Use context manager for admin operations
    with PermissionContext(admin_permissions):
        try:
            # Admin can do anything
            accounts = list(client.accounts.list(page_size=2))
            print(f"Admin accessed {len(accounts)} accounts")
        except PermissionError as e:
            print(f"Admin permission denied: {e}")
    
    # Switch to viewer context
    with PermissionContext(viewer_permissions):
        try:
            # Viewer can read
            accounts = list(client.accounts.list(page_size=2))
            print(f"Viewer accessed {len(accounts)} accounts")
            
            # But viewer cannot create (this would fail)
            # client.accounts.create({...})  # Would raise PermissionError
            
        except PermissionError as e:
            print(f"Viewer permission denied: {e}")


def example_custom_permissions():
    """Example of custom permission configurations."""
    print("\n=== Custom Permissions ===")
    
    # Create custom permissions for a user
    custom_permissions = create_user_permissions(
        "special_user",
        Role.VIEWER,  # Base role
        custom_overrides={
            # Override: Give this viewer write access to campaigns
            ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
            # And admin access to events
            ResourceType.EVENTS: {Permission.ADMIN}
        }
    )
    
    client.set_user_permissions(custom_permissions)
    
    # Check what permissions the user has
    campaign_perms = custom_permissions.resource_permissions.get(ResourceType.CAMPAIGNS, set())
    event_perms = custom_permissions.resource_permissions.get(ResourceType.EVENTS, set())
    
    print(f"User has campaign permissions: {[p.value for p in campaign_perms]}")
    print(f"User has event permissions: {[p.value for p in event_perms]}")


def example_permission_config():
    """Example of using permission configuration."""
    print("\n=== Permission Configuration ===")
    
    # Create a permission configuration
    config = PermissionConfig()
    
    # Add users to the configuration
    config.add_user("fundraiser1", Role.FUNDRAISER)
    config.add_user("admin1", Role.ADMIN)
    config.add_user("event_manager1", Role.EVENT_MANAGER)
    
    # Create a client with the configuration
    client_with_config = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        permission_config=config
    )
    
    # Set user by ID (looks up in configuration)
    if client_with_config.set_user_by_id("fundraiser1"):
        print("Successfully set user permissions from config")
        
        # Get current user's permissions for donations
        perms = config.get_effective_permissions("fundraiser1", ResourceType.DONATIONS)
        print(f"Fundraiser1 donation permissions: {[p.value for p in perms]}")
    else:
        print("User not found in configuration")
    
    # List all users with donation write permission
    users_with_write = config.list_users_with_permission(ResourceType.DONATIONS, Permission.WRITE)
    print(f"Users who can create donations: {users_with_write}")


def example_error_handling():
    """Example of handling permission errors."""
    print("\n=== Error Handling ===")
    
    # Create a viewer (read-only) user
    viewer = create_user_permissions("readonly_user", Role.VIEWER)
    client.set_user_permissions(viewer)
    
    try:
        # This should work
        accounts = list(client.accounts.list(page_size=1))
        print("✓ Read operation succeeded")
        
    except PermissionError as e:
        print(f"✗ Read failed: {e}")
    
    try:
        # This should fail - viewers can't create
        # client.accounts.create({"accountType": "INDIVIDUAL", "firstName": "Test", "lastName": "User"})
        print("✗ This line shouldn't execute - create should have failed")
        
    except PermissionError as e:
        print(f"✓ Create operation properly blocked: {e.resource.value} - {e.permission.value}")


def main():
    """Run all governance examples."""
    print("Neon CRM SDK Governance Examples")
    print("=" * 40)
    
    try:
        example_basic_usage()
        example_with_context_manager()
        example_custom_permissions()
        example_permission_config()
        example_error_handling()
        
    except Exception as e:
        print(f"Example failed: {e}")
        print("Make sure to set NEON_ORG_ID and NEON_API_KEY environment variables")


if __name__ == "__main__":
    main()