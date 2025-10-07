# Permissions and Access Control

The Neon CRM SDK includes a comprehensive governance system that provides role-based access control (RBAC) for all API operations. This document explains how to configure and use the permission system.

## Table of Contents

- [Quick Start](#quick-start)
- [Why Use Permissions?](#why-use-permissions)
- [Configuration Methods](#configuration-methods)
- [Available Roles](#available-roles)
- [Permission Types](#permission-types)
- [Resource Types](#resource-types)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

## Quick Start

### Simple Role-Based Setup (Recommended)

The easiest way to use permissions is to specify a role when creating the client:

```python
from neon_crm import NeonClient

# Create a client with viewer (read-only) permissions
# Governance is enabled by default
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"
)

# All operations are automatically checked against viewer permissions
accounts = list(client.accounts.list())  # ✓ Allowed - viewers can read
# client.accounts.create({...})          # ✗ Blocked - viewers can't create
```

### Using Environment Variables

You can configure permissions using environment variables in your `.env` file:

```bash
NEON_ORG_ID=your_org_id
NEON_API_KEY=your_api_key
NEON_DEFAULT_ROLE=editor
```

Then simply create the client without parameters:

```python
client = NeonClient()  # Automatically uses role from .env
```

### Role with Permission Overrides

Start with a base role and customize specific resources:

```python
client = NeonClient(
    default_role="viewer",  # Base: read-only
    permission_overrides={
        "donations": {"read", "write"},  # Can create donations
        "campaigns": {"read", "write"}   # Can create campaigns
    }
)
```

## Why Use Permissions?

The governance system provides several benefits:

1. **Security**: Prevent unauthorized operations on sensitive data
2. **Multi-user Applications**: Different users can have different access levels
3. **Testing**: Test your application with restricted permissions
4. **Compliance**: Enforce organizational access policies
5. **Safety**: Prevent accidental data modifications

**Note**: Governance is **enabled by default** with the 'viewer' (read-only) role. To use different permissions, specify `default_role` when creating the client or set the `NEON_DEFAULT_ROLE` environment variable. To disable governance entirely (not recommended), set `enable_governance=False`.

## Configuration Methods

There are three ways to configure permissions, from simplest to most advanced:

### 1. Simple Role (Recommended for Most Cases)

Specify a role name when creating the client:

```python
client = NeonClient(
    default_role="fundraiser"  # or 'viewer', 'editor', 'admin', etc.
)
```

### 2. Role with Overrides

Customize permissions for specific resources:

```python
from neon_crm import Permission
from neon_crm.governance import ResourceType

client = NeonClient(
    default_role="viewer",
    permission_overrides={
        ResourceType.DONATIONS: {Permission.READ, Permission.WRITE},
        # Can also use strings:
        "events": {"read", "write", "update"}
    }
)
```

### 3. Advanced: Multiple Clients with Different Roles

For complex scenarios where you need different permission levels:

```python
# Create separate clients for different operations
admin_client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="admin"
)

viewer_client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"
)

# Use appropriate client for each operation
admin_client.accounts.create({...})  # Admin operations
data = list(viewer_client.accounts.list())  # Read-only operations
```

## Available Roles

The SDK provides six predefined roles:

### Viewer (Read-Only)
- **Use case**: Data analysts, report viewers
- **Access**: Read-only access to most resources
- **Example**:
  ```python
  client = NeonClient(default_role="viewer")
  ```

### Editor
- **Use case**: Staff who need to create and update records
- **Access**: Read and write access to most resources
- **Restrictions**: Cannot create orders/payments directly, no access to system configuration
- **Example**:
  ```python
  client = NeonClient(default_role="editor")
  ```

### Admin
- **Use case**: System administrators
- **Access**: Full access to all resources including deletion and configuration
- **Example**:
  ```python
  client = NeonClient(default_role="admin")
  ```

### Fundraiser
- **Use case**: Fundraising staff
- **Access**: Full access to donations, pledges, campaigns, grants, and related resources
- **Read-only**: Events, memberships, volunteers
- **Example**:
  ```python
  client = NeonClient(default_role="fundraiser")
  ```

### Event Manager
- **Use case**: Event coordinators
- **Access**: Full access to events, including deletion
- **Additional**: Can manage accounts, volunteers, activities
- **Read-only**: Donations, memberships, campaigns
- **Example**:
  ```python
  client = NeonClient(default_role="event_manager")
  ```

### Volunteer Coordinator
- **Use case**: Volunteer program managers
- **Access**: Full access to volunteers, including deletion
- **Additional**: Can manage accounts, activities
- **Read-only**: Events, donations, memberships
- **Example**:
  ```python
  client = NeonClient(default_role="volunteer_coordinator")
  ```

## Permission Types

Each resource can have the following permissions:

| Permission | Description | Example Operations |
|------------|-------------|-------------------|
| `READ` | View existing records | List accounts, search donations |
| `WRITE` | Create new records | Create account, add donation |
| `UPDATE` | Modify existing records | Update account details, change donation amount |
| `DELETE` | Remove records | Delete account, remove event |
| `ADMIN` | Full access | All operations including sensitive actions |

## Resource Types

The governance system controls access to these resources:

- `accounts` - Individual and organization accounts
- `activities` - Account activities and interactions
- `addresses` - Contact addresses
- `campaigns` - Fundraising campaigns
- `custom_fields` - Custom field definitions
- `custom_objects` - Custom object definitions
- `donations` - Financial contributions
- `events` - Events and registrations
- `grants` - Grant tracking
- `households` - Household groupings
- `memberships` - Membership records
- `online_store` - Store configuration
- `orders` - Purchase orders
- `payments` - Payment processing
- `pledges` - Donation pledges
- `properties` - System properties
- `recurring_donations` - Recurring donation schedules
- `soft_credits` - Soft credit allocations
- `volunteers` - Volunteer records
- `webhooks` - Webhook configurations

## Advanced Usage

### Dynamically Changing Permissions

For scenarios where you need to change permissions during runtime, use `set_user_permissions()`:

```python
from neon_crm.governance import create_user_permissions, Role

# Create client with initial role
client = NeonClient(default_role="viewer")

# Later, upgrade to admin permissions
from neon_crm.governance import create_user_permissions, Role
admin_perms = create_user_permissions("admin_user", Role.ADMIN)
client.set_user_permissions(admin_perms)

# Now operations run with admin permissions
client.accounts.create({...})
client.donations.update(donation_id, {...})
```

**Note**: For most use cases, creating separate clients with different roles is clearer and more maintainable.

### Multi-User Configuration

For applications with multiple users:

```python
from neon_crm.governance import PermissionConfig, Role

# Create a permission configuration
config = PermissionConfig()

# Add users with different roles
config.add_user("fundraiser_1", Role.FUNDRAISER)
config.add_user("admin_1", Role.ADMIN)
config.add_user("viewer_1", Role.VIEWER)

# Create client with the configuration
client = NeonClient(permission_config=config)

# Switch users dynamically
client.set_user_by_id("fundraiser_1")
# Now client operates with fundraiser permissions

client.set_user_by_id("admin_1")
# Now client operates with admin permissions
```

### Checking Permissions

You can check permissions before attempting operations:

```python
from neon_crm import Permission
from neon_crm.governance import ResourceType

# Check if client has permission
if client.user_permissions and client.user_permissions.has_permission(
    ResourceType.DONATIONS,
    Permission.WRITE
):
    client.donations.create({...})
else:
    print("Permission denied: Cannot create donations")
```

### Custom Permission Configuration File

Save and load permission configurations:

```python
config = PermissionConfig()
config.add_user("user1", Role.EDITOR)
config.add_user("user2", Role.VIEWER)

# Save to file
config.save_to_file("~/.neon/permissions.json")

# Load from file
config2 = PermissionConfig(config_file="~/.neon/permissions.json")
```

## Best Practices

### 1. Use Environment Variables for Configuration

Store permissions configuration in environment variables:

```bash
# .env file
NEON_DEFAULT_ROLE=viewer
NEON_ENABLE_GOVERNANCE=true
```

This makes it easy to change permissions without modifying code.

### 2. Start with Least Privilege

Begin with the most restrictive role and add permissions as needed:

```python
# Start with viewer
client = NeonClient(
    default_role="viewer",
    permission_overrides={
        # Only add permissions you specifically need
        "donations": {"read", "write"}
    }
)
```

### 3. Use Roles Instead of Custom Permissions

Prefer predefined roles over custom permission configurations:

```python
# ✓ Good: Use a role
client = NeonClient(default_role="fundraiser")

# ✗ Avoid: Building permissions from scratch
# (unless you have specific requirements)
```

### 4. Use Appropriate Roles in Production

For production applications, use environment variables to configure roles:

```python
# Production configuration
client = NeonClient(
    default_role=os.getenv("NEON_DEFAULT_ROLE", "viewer")
)
```

### 5. Document Permission Requirements

Document what permissions your application needs:

```python
"""
This application requires the following permissions:
- READ access to accounts, donations, campaigns
- WRITE access to activities
- UPDATE access to accounts

Recommended role: editor
Or use: default_role="viewer" with permission_overrides for activities
"""
```

### 6. Test with Different Roles

Test your application with different permission levels:

```python
# Test with different roles
for role in ["viewer", "editor", "fundraiser"]:
    client = NeonClient(default_role=role)
    # Run your tests...
```

## Examples

See the following files for detailed examples:

- `examples/governance_example.py` - Comprehensive governance examples
- `examples/basic_usage.ipynb` - Simple role-based usage in notebooks

## Disabling Governance

Governance is enabled by default for security. To disable governance (not recommended):

```python
# Explicitly disable governance (not recommended for production)
client = NeonClient(enable_governance=False)
```

**Warning**: Disabling governance removes all permission checks and allows unrestricted access to all operations. Only disable governance if you have alternative security measures in place.

## Usage Patterns

### Simple Pattern (Recommended)

For most applications, just specify a role:

```python
# Single role for entire application
client = NeonClient(default_role="editor")

# All operations use editor permissions
accounts = list(client.accounts.list())
client.donations.create({...})
```

### Multi-Role Pattern

For applications needing different permission levels:

```python
# Create specialized clients
read_client = NeonClient(default_role="viewer")
write_client = NeonClient(default_role="editor")

# Use appropriate client for each operation
data = list(read_client.accounts.list())  # Read operations
write_client.donations.create({...})       # Write operations
```

### Dynamic Permission Pattern

For applications where permissions change at runtime:

```python
from neon_crm import Role
from neon_crm.governance import create_user_permissions

client = NeonClient(default_role="viewer")

# Change permissions dynamically
def elevate_to_admin():
    admin_perms = create_user_permissions("admin", Role.ADMIN)
    client.set_user_permissions(admin_perms)

elevate_to_admin()
client.accounts.create({...})  # Now has admin permissions
```

## Troubleshooting

### Permission Denied Errors

If you get permission denied errors:

1. Check which role is configured:
   ```python
   print(f"Governance enabled: {client.governance_enabled}")
   if client.user_permissions:
       print(f"Role: {client.user_permissions.role}")
   ```

2. Verify the operation is allowed for your role:
   ```python
   from neon_crm.governance import ResourceType, Permission

   can_create = client.user_permissions.has_permission(
       ResourceType.DONATIONS,
       Permission.WRITE
   )
   print(f"Can create donations: {can_create}")
   ```

3. Add permission override if needed:
   ```python
   client = NeonClient(
       default_role="viewer",
       permission_overrides={
           "donations": {"read", "write"}  # Add write permission
       },
       enable_governance=True
   )
   ```

### Governance Not Working

If governance isn't being enforced:

1. Check if governance is enabled:
   ```python
   print(client.governance_enabled)  # Should be True
   ```

2. Enable governance explicitly:
   ```python
   client = NeonClient(enable_governance=True)
   # Or set environment variable: NEON_ENABLE_GOVERNANCE=true
   ```

## Additional Resources

- [API Documentation](https://docs.neoncrm.com/api/)
- [Configuration Guide](getting-started/configuration.md)
- [Quick Start Guide](getting-started/quickstart.md)

## Support

For questions or issues with the governance system:

1. Check the examples in `examples/governance_example.py`
2. Review this documentation
3. Open an issue on GitHub with details about your use case
