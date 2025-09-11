# Neon CRM Python SDK

A comprehensive, high-quality Python SDK for the Neon CRM API v2.

## Features

- **Full API Coverage**: Support for all 33+ Neon CRM API resource categories
- **Type Safety**: Built with Pydantic models for full type safety and validation
- **Async/Await Support**: Both synchronous and asynchronous clients
- **Automatic Pagination**: Easy iteration over paginated results
- **Advanced Search**: Support for Neon's flexible search capabilities
- **Custom Objects**: Full support for Neon's custom object framework
- **Error Handling**: Comprehensive error handling with specific exception types
- **Rate Limiting**: Built-in rate limit handling and retries
- **Access Control**: Built-in governance system with role-based permissions
- **Modern Python**: Supports Python 3.8+

## Installation

```bash
pip install neon-crm
```

## Quick Start

```python
from neon_crm import NeonClient

# Initialize the client
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    environment="production"  # or "trial"
)

# Get accounts
accounts = client.accounts.list(page_size=50)
for account in accounts:
    print(f"{account.firstName} {account.lastName}")

# Search for accounts
search_results = client.accounts.search({
    "searchFields": [
        {"field": "Email", "operator": "EQUAL", "value": "john@example.com"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email"]
})

# Create a new account
new_account = client.accounts.create({
    "individualAccount": {
        "accountType": "INDIVIDUAL",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com"
    }
})

# Get donations for an account
donations = client.accounts.get_donations(account_id=12345)
```

## Access Control & Governance

The SDK includes a comprehensive governance system for controlling user access to different resources and actions:

```python
from neon_crm.governance import Role, create_user_permissions

# Set up user permissions
fundraiser_permissions = create_user_permissions("user123", Role.FUNDRAISER)
client.set_user_permissions(fundraiser_permissions)

# All API calls will now be checked against user permissions
try:
    accounts = list(client.accounts.list())  # ✓ Allowed for fundraisers
    donations = client.donations.create(data)  # ✓ Allowed for fundraisers
    # client.accounts.delete(123)  # ✗ Would raise PermissionError
except PermissionError as e:
    print(f"Access denied: {e}")
```

### Available Roles
- **VIEWER** - Read-only access
- **EDITOR** - Read and modify most resources
- **FUNDRAISER** - Full access to donation-related activities  
- **EVENT_MANAGER** - Full control over events and registrations
- **VOLUNTEER_COORDINATOR** - Manage volunteers and activities
- **ADMIN** - Full access to all resources

### Custom Permissions
```python
from neon_crm.governance import ResourceType, Permission

# Create custom permissions
custom_permissions = create_user_permissions(
    "special_user",
    Role.VIEWER,  # Base role
    custom_overrides={
        ResourceType.EVENTS: {Permission.ADMIN},  # Full event access
        ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE}  # Campaign write access
    }
)
```

See [GOVERNANCE.md](GOVERNANCE.md) for complete documentation.

## Async Usage

```python
import asyncio
from neon_crm import AsyncNeonClient

async def main():
    async with AsyncNeonClient(
        org_id="your_org_id",
        api_key="your_api_key"
    ) as client:
        accounts = await client.accounts.list(page_size=50)
        async for account in accounts:
            print(f"{account.firstName} {account.lastName}")

asyncio.run(main())
```

## API Resources

The SDK provides access to all Neon CRM API resources:

- **Accounts** - Contact and organization management
- **Donations** - Donation tracking and management
- **Events** - Event management (legacy events)
- **Memberships** - Membership management
- **Activities** - Activity tracking
- **Custom Objects** - Custom object framework
- **Volunteers** - Volunteer management
- **Campaigns** - Campaign management
- **And 25+ more resources**

## Authentication

The Neon CRM API uses HTTP Basic Authentication:

- **Username**: Your Neon organization ID
- **Password**: Your API key

```python
client = NeonClient(
    org_id="12345",  # Your organization ID
    api_key="your-api-key-here"
)
```

## Error Handling

The SDK provides specific exception types for different error conditions:

```python
from neon_crm import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonNotFoundError,
    NeonRateLimitError
)

try:
    account = client.accounts.get(account_id=12345)
except NeonNotFoundError:
    print("Account not found")
except NeonAuthenticationError:
    print("Invalid credentials")
except NeonRateLimitError:
    print("Rate limit exceeded, please wait")
except NeonAPIError as e:
    print(f"API error: {e.message}")
```

## Configuration

### Environment Variables

You can set your credentials as environment variables:

```bash
export NEON_ORG_ID="your_org_id"
export NEON_API_KEY="your_api_key"
export NEON_ENVIRONMENT="production"  # or "trial"
```

```python
# Client will automatically use environment variables
client = NeonClient()
```

### Custom Configuration

```python
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    environment="production",  # "production" or "trial"
    timeout=30.0,  # Request timeout in seconds
    max_retries=3,  # Number of retries for failed requests
    api_version="2.10"  # API version (latest by default)
)
```

## Development

### Setup

```bash
git clone https://github.com/your-username/neon-crm-python.git
cd neon-crm-python
pip install -e ".[dev]"
pre-commit install
```

### Testing

```bash
pytest
```

### Type Checking

```bash
mypy src/neon_crm
```

### Code Formatting

```bash
black src/ tests/
ruff src/ tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [Full documentation](https://neon-crm-python.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-username/neon-crm-python/issues)
- **Neon CRM API Docs**: [Official API Documentation](https://developer.neoncrm.com/api/general/)