# Using Governance in Notebooks

This guide explains how to use the governance and access control system in Jupyter notebooks and analysis scripts.

## Overview

The Neon CRM SDK includes a comprehensive governance system that enforces role-based access control for all API operations. Governance is enabled by default to ensure secure operations.

## Basic Setup

### Simple Setup (Recommended)

Initialize the client with a role - governance is automatic:

```python
from neon_crm import NeonClient

# Create client with viewer (read-only) role for analysis
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"  # Read-only for safety
)

# All operations are automatically permission-checked
accounts = list(client.accounts.list(page_size=10))
donations = list(client.donations.search(search_request))
```

### Import Governance Components (Optional)

Only needed for advanced permission checking:

```python
# Import directly from the main package (preferred)
from neon_crm import Permission, Role

# Or import from governance submodule
from neon_crm.governance import ResourceType
```

## Available Roles

### Predefined Roles

Choose the role that matches your notebook's purpose:

- **viewer**: Read-only access (recommended for analysis notebooks)
- **editor**: Read/write access to most resources
- **admin**: Full access to all resources
- **fundraiser**: Full access to donation-related resources
- **event_manager**: Full access to events
- **volunteer_coordinator**: Full access to volunteers

### Permission Types

- **READ**: Get and search operations
- **WRITE**: Create new resources
- **UPDATE**: Modify existing resources
- **DELETE**: Delete resources
- **ADMIN**: Full access including sensitive operations

## Best Practices for Notebooks

### 1. Use Viewer Role for Analysis

For data analysis notebooks, use the viewer role:

```python
# Analysis notebook setup
client = NeonClient(default_role="viewer")

print(f"🔐 Governance enabled: {client.governance_enabled}")
print(f"👤 Role: viewer (read-only)")
print("✅ Safe for data analysis - no accidental modifications")
```

### 2. Use Editor/Admin for Data Entry Notebooks

For notebooks that create or update data:

```python
# Data entry notebook setup
client = NeonClient(default_role="editor")

# Can now create and update records
new_account = client.accounts.create({...})
```

### 3. Use Permission Overrides for Specific Needs

Start with a restrictive role and add specific permissions:

```python
# Mostly read-only, but can create activities
client = NeonClient(
    default_role="viewer",
    permission_overrides={
        "activities": {"read", "write"}  # Can log activities
    }
)
```

## Complete Notebook Example

```python
import os
import pandas as pd
from neon_crm import NeonClient
from neon_crm.exceptions import NeonAPIError

# Setup client with appropriate role
client = NeonClient(
    org_id=os.getenv("NEON_ORG_ID"),
    api_key=os.getenv("NEON_API_KEY"),
    default_role="viewer"  # Read-only for analysis
)

print("✅ Neon CRM client initialized")
print(f"🔐 Role: {client.user_permissions.role if client.user_permissions else 'viewer'}")

# Fetch data safely
try:
    # This works - viewers can read
    accounts = list(client.accounts.list(page_size=100))
    print(f"📊 Retrieved {len(accounts)} accounts")

    # Convert to DataFrame for analysis
    df = pd.DataFrame(accounts)

    # Perform analysis...

except NeonAPIError as e:
    print(f"❌ API Error: {e.message}")

# Attempting to create would fail (viewer role)
try:
    # This would be blocked
    # client.accounts.create({...})
    pass
except PermissionError as e:
    print(f"🔒 Permission denied (as expected): {e}")
```

## Resource Types

The governance system covers all resource types:

- accounts, activities, addresses, campaigns
- custom_fields, custom_objects, donations, events
- grants, households, memberships, online_store
- orders, payments, pledges, properties
- recurring_donations, soft_credits, volunteers, webhooks

## Checking Permissions

You can check permissions before attempting operations:

```python
from neon_crm import Permission
from neon_crm.governance import ResourceType

# Check if we can create donations
if client.user_permissions.has_permission(
    ResourceType.DONATIONS,
    Permission.WRITE
):
    client.donations.create({...})
else:
    print("Cannot create donations with current role")
```

## Different Roles for Different Sections

For notebooks with different security needs in different sections, create multiple clients:

```python
# Read-only client for analysis
read_client = NeonClient(default_role="viewer")

# Write client for data updates (use sparingly)
write_client = NeonClient(default_role="editor")

# Analysis section
data = list(read_client.accounts.list())
# ... perform analysis ...

# Update section (clearly marked)
print("⚠️  Entering write section - data will be modified")
write_client.accounts.update(account_id, new_data)
```

## Error Handling

Always wrap operations in try-except blocks:

```python
from neon_crm.exceptions import NeonAPIError
from neon_crm.governance.access_control import PermissionError

try:
    # Attempt operation
    result = client.accounts.create({...})

except PermissionError as e:
    print(f"🔒 Permission denied: {e}")
    print("💡 Tip: Check your role or use permission_overrides")

except NeonAPIError as e:
    print(f"❌ API Error: {e.message}")
```

## Tips for Safe Notebooks

1. **Default to Viewer**: Use viewer role unless you specifically need write access
2. **Clear Sections**: Clearly mark sections that modify data
3. **Test First**: Run analysis cells first to verify before write operations
4. **Use Overrides**: Use permission_overrides for fine-grained control
5. **Environment Variables**: Store role in .env file for easy configuration

## Environment Variable Configuration

Create a `.env` file:

```bash
NEON_ORG_ID=your_org_id
NEON_API_KEY=your_api_key
NEON_DEFAULT_ROLE=viewer
```

Then in your notebook:

```python
from neon_crm import NeonClient

# Automatically uses settings from .env
client = NeonClient()
```

## Additional Resources

- [Complete Permissions Documentation](permissions.md)
- [Basic Usage Examples](examples/basic.md)
