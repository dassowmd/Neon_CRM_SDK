# Neon CRM SDK Governance System

The Neon CRM SDK includes a comprehensive governance and access control system that allows you to control who can access what resources and perform which actions.

## Overview

The governance system provides:

- **Role-based access control** with pre-defined roles
- **Resource-level permissions** for fine-grained control
- **Action-specific permissions** (read, write, update, delete, admin)
- **Custom permission overrides** for specific users
- **Configuration management** via JSON files
- **Runtime permission checking** with clear error messages

## Quick Start

```python
from neon_crm import NeonClient
from neon_crm.governance import Role, create_user_permissions

# Create client
client = NeonClient(org_id="your_org", api_key="your_key")

# Set user permissions
permissions = create_user_permissions("user123", Role.FUNDRAISER)
client.set_user_permissions(permissions)

# Now all operations will be checked against user permissions
accounts = list(client.accounts.list())  # ✓ Allowed for fundraisers
```

## Permission Levels

### Available Permissions

- **READ** - View resources
- **WRITE** - Create new resources
- **UPDATE** - Modify existing resources
- **DELETE** - Remove resources
- **ADMIN** - Full access (includes all other permissions)

### Pre-defined Roles

#### VIEWER
- Read-only access to most resources
- No creation, modification, or deletion rights
- Suitable for reporting and analysis users

#### EDITOR
- Read and modify access to most resources
- Cannot delete sensitive data
- Cannot access system configuration
- Suitable for general staff members

#### FUNDRAISER
- Full access to donation-related resources
- Read access to accounts, events, and volunteers
- Optimized for fundraising activities

#### EVENT_MANAGER
- Full control over events
- Manage event registrations and volunteers
- Read access to related resources

#### VOLUNTEER_COORDINATOR
- Full control over volunteer management
- Manage volunteer activities and assignments
- Read access to events and accounts

#### ADMIN
- Full access to all resources
- Can perform any action
- Should be used sparingly

## Usage Examples

### Basic Usage

```python
from neon_crm import NeonClient
from neon_crm.governance import create_user_permissions, Role

client = NeonClient(org_id="your_org", api_key="your_key")

# Create fundraiser permissions
fundraiser = create_user_permissions("fundraiser_id", Role.FUNDRAISER)
client.set_user_permissions(fundraiser)

try:
    # This works - fundraisers can read accounts
    accounts = list(client.accounts.list())

    # This works - fundraisers can create donations
    donation = client.donations.create(donation_data)

    # This fails - fundraisers can't delete accounts
    # client.accounts.delete(123)  # Raises PermissionError

except PermissionError as e:
    print(f"Access denied: {e}")
```

### Custom Permissions

```python
from neon_crm.governance import ResourceType, Permission

# Create user with custom permissions
custom_permissions = create_user_permissions(
    "special_user",
    Role.VIEWER,  # Base role
    custom_overrides={
        # Give this viewer admin access to events
        ResourceType.EVENTS: {Permission.ADMIN},
        # And write access to campaigns
        ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE, Permission.UPDATE}
    }
)

client.set_user_permissions(custom_permissions)
```

### Context Managers

```python
from neon_crm.governance import PermissionContext

admin_permissions = create_user_permissions("admin", Role.ADMIN)
viewer_permissions = create_user_permissions("viewer", Role.VIEWER)

# Temporarily elevate permissions
with PermissionContext(admin_permissions):
    # Admin operations here
    sensitive_data = client.webhooks.list()

# Back to normal permissions
with PermissionContext(viewer_permissions):
    # Read-only operations
    accounts = client.accounts.list()
```

### Configuration Files

```python
from neon_crm.governance import PermissionConfig

# Load from JSON configuration
config = PermissionConfig("/path/to/config.json")

client = NeonClient(
    org_id="your_org",
    api_key="your_key",
    permission_config=config
)

# Set user by ID (looks up in config)
client.set_user_by_id("john_fundraiser")
```

Example configuration file:

```json
{
  "users": {
    "john_fundraiser": {
      "role": "fundraiser",
      "permissions": {
        "events": ["read"],
        "volunteers": ["read", "write"]
      }
    },
    "sarah_admin": {
      "role": "admin"
    }
  },
  "role_overrides": {
    "editor": {
      "webhooks": ["read", "write", "update"]
    }
  }
}
```

## Resource Types

The system controls access to these resources:

- **ACCOUNTS** - Individual and company contacts
- **ACTIVITIES** - Activity tracking
- **CAMPAIGNS** - Fundraising campaigns
- **CUSTOM_FIELDS** - Custom field definitions
- **CUSTOM_OBJECTS** - Custom object definitions
- **DONATIONS** - Donation records
- **EVENTS** - Events and registrations
- **GRANTS** - Grant management
- **HOUSEHOLDS** - Household groupings
- **MEMBERSHIPS** - Membership management
- **ONLINE_STORE** - Online store items
- **ORDERS** - Purchase orders
- **PAYMENTS** - Payment processing
- **PLEDGES** - Pledge commitments
- **PROPERTIES** - System properties
- **RECURRING_DONATIONS** - Recurring donation setup
- **SOFT_CREDITS** - Soft credit assignments
- **VOLUNTEERS** - Volunteer management
- **WEBHOOKS** - Webhook configuration

## Error Handling

When a user lacks required permissions, a `PermissionError` is raised:

```python
from neon_crm.governance import PermissionError

try:
    client.accounts.create(account_data)
except PermissionError as e:
    print(f"Permission denied: {e}")
    print(f"Resource: {e.resource.value}")
    print(f"Required permission: {e.permission.value}")
    print(f"User: {e.user_id}")
```

## Configuration Management

### Creating Configuration

```python
from neon_crm.governance import PermissionConfig, Role

config = PermissionConfig()

# Add users
config.add_user("user1", Role.FUNDRAISER)
config.add_user("user2", Role.ADMIN)

# Save to file
config.save_to_file("permissions.json")
```

### Loading Configuration

```python
# Load from file
config = PermissionConfig("permissions.json")

# Use with client
client = NeonClient(permission_config=config)
client.set_user_by_id("user1")
```

### Querying Permissions

```python
# Check effective permissions
perms = config.get_effective_permissions("user1", ResourceType.DONATIONS)
print(f"User permissions: {[p.value for p in perms]}")

# List users with specific permission
users = config.list_users_with_permission(ResourceType.ACCOUNTS, Permission.WRITE)
print(f"Users who can create accounts: {users}")
```

## Integration

The governance system integrates seamlessly with the existing SDK:

1. **Automatic checking** - All resource methods automatically check permissions
2. **Context preservation** - Permissions are maintained throughout request chains
3. **Clear errors** - Detailed error messages when access is denied
4. **Backward compatibility** - Works with existing code (no governance = no restrictions)

## Best Practices

1. **Principle of least privilege** - Give users only the permissions they need
2. **Use pre-defined roles** when possible rather than custom permissions
3. **Regular audits** - Review user permissions periodically
4. **Configuration files** for production environments
5. **Test permissions** thoroughly before deploying
6. **Handle PermissionError** gracefully in your applications

## Advanced Usage

### Custom Permission Rules

```python
# Check permissions programmatically
from neon_crm.governance import check_permission, ResourceType, Permission

if check_permission(ResourceType.DONATIONS, Permission.WRITE):
    # User can create donations
    pass
```

### Role Updates

```python
# Update role permissions globally
config.update_role_permissions(
    Role.EDITOR,
    ResourceType.WEBHOOKS,
    {Permission.READ, Permission.WRITE}
)
```

### Multiple Clients

```python
# Different clients for different users
admin_client = NeonClient(user_permissions=admin_permissions)
user_client = NeonClient(user_permissions=user_permissions)
```

This governance system provides the flexible, secure access control your Neon CRM integration needs while maintaining the simplicity and power of the SDK.
