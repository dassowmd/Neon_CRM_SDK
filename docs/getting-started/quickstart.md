# Quickstart Guide

Get up and running with the Neon CRM SDK in minutes.

## Installation

```bash
pip install neon-crm-sdk
```

Or install from source:

```bash
git clone https://github.com/yourusername/neon-crm-sdk.git
cd neon-crm-sdk
pip install -e .
```

## Configuration

The SDK can be configured in three ways:

### 1. Environment Variables (Recommended)

```bash
export NEON_ORG_ID="your-org-id"
export NEON_API_KEY="your-api-key"
export NEON_ENVIRONMENT="production"  # or "trial"
```

### 2. Configuration File

Create `~/.neon/config.json`:

```json
{
  "profiles": {
    "default": {
      "org_id": "your-org-id",
      "api_key": "your-api-key",
      "environment": "production"
    }
  }
}
```

### 3. Direct Initialization

```python
from neon_crm import NeonClient

client = NeonClient(
    org_id="your-org-id",
    api_key="your-api-key",
    environment="production"
)
```

## Basic Usage

### Initialize the Client

```python
from neon_crm import NeonClient

# Uses environment variables or config file
client = NeonClient()
```

### Search for Accounts

```python
# Simple search
search_request = {
    "searchFields": [
        {"field": "Account Type", "operator": "EQUAL", "value": "Individual"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"],
    "pagination": {"currentPage": 0, "pageSize": 10}
}

accounts = list(client.accounts.search(search_request))
for account in accounts:
    print(f"{account['First Name']} {account['Last Name']}")
```

### Get a Specific Account

```python
account_id = 12345
account = client.accounts.retrieve(account_id)
print(account)
```

### Search for Donations

```python
from datetime import datetime, timedelta

# Get donations from the last 30 days
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

search_request = {
    "searchFields": [
        {"field": "Donation Date", "operator": "GREATER_AND_EQUAL", "value": start_date}
    ],
    "outputFields": ["Donation ID", "Account ID", "Donation Amount", "Donation Date"],
    "pagination": {"currentPage": 0, "pageSize": 50}
}

donations = list(client.donations.search(search_request))
total = sum(float(d.get('Donation Amount', 0)) for d in donations)
print(f"Total donations in last 30 days: ${total:,.2f}")
```

### Create an Account

```python
new_account = {
    "individualAccount": {
        "accountCustomFields": [],
        "primaryContact": {
            "firstName": "Jane",
            "lastName": "Doe",
            "email1": "jane.doe@example.com",
            "addresses": [
                {
                    "addressType": "Home",
                    "city": "San Francisco",
                    "stateProvince": {"code": "CA"},
                    "country": {"name": "United States"}
                }
            ]
        }
    }
}

result = client.accounts.create(new_account)
print(f"Created account ID: {result['id']}")
```

## Governance & Permissions

The SDK includes a built-in governance system to control access to resources.

### Setting Default Role

```python
from neon_crm import NeonClient

# Initialize with read-only access
client = NeonClient(default_role="viewer")

# Fundraiser role has access to donations and accounts
client = NeonClient(default_role="fundraiser")

# Admin role has full access
client = NeonClient(default_role="admin")
```

### Available Roles

- **viewer**: Read-only access to most resources
- **editor**: Read and write access to most resources
- **admin**: Full access to all resources
- **fundraiser**: Full access to donations, accounts, campaigns, pledges
- **event_manager**: Full access to events, registrations, attendees
- **volunteer_coordinator**: Full access to volunteers and activities

### Custom Permission Overrides

```python
from neon_crm.governance import ResourceType, Permission

client = NeonClient(
    default_role="viewer",
    permission_overrides={
        ResourceType.DONATIONS: {Permission.READ, Permission.WRITE}
    }
)
```

### Disabling Governance

```python
# For development/testing only
client = NeonClient(enable_governance=False)
```

## Error Handling

```python
from neon_crm.exceptions import NeonAPIError, NeonValidationError

try:
    account = client.accounts.retrieve(12345)
except NeonAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
except NeonValidationError as e:
    print(f"Validation Error: {e}")
```

## Pagination

The SDK automatically handles pagination for search operations:

```python
# This will automatically fetch all pages
all_accounts = list(client.accounts.search(search_request))

# Or limit the number of results
from itertools import islice

first_100 = list(islice(client.accounts.search(search_request), 100))
```

## Next Steps

- Read the [Configuration Guide](configuration.md) for detailed setup options
- Check out [Examples](../examples/basic.md) for more usage patterns
- See [User Guide](../user-guide/basic-usage.md) for comprehensive documentation
- Review the [API Reference](../api/client.md) for detailed API documentation

## Getting Help

- 📖 [Documentation](https://github.com/yourusername/neon-crm-sdk/docs)
- 🐛 [Issue Tracker](https://github.com/yourusername/neon-crm-sdk/issues)
- 💬 [Discussions](https://github.com/yourusername/neon-crm-sdk/discussions)

## Common Issues

### Authentication Errors

If you see "Authentication required" errors, ensure:
1. Your API credentials are properly configured
2. You have the correct `default_role` set for the resources you're accessing
3. Your API key has the necessary permissions in Neon CRM

### Field Name Errors

The Neon API uses display names for fields (e.g., "First Name" not "firstName"). Use the exact field names as they appear in the Neon CRM web interface.

### Rate Limiting

The SDK includes automatic retry logic for rate-limited requests. If you encounter persistent rate limiting:
- Reduce the page size in searches
- Add delays between bulk operations
- Consider using the async client for better concurrency control
