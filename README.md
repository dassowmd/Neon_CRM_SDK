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
- **Modern Python**: Supports Python 3.8+

## Installation

```bash
pip install neon-crm
```

## Quick Start

```python
from neon_crm import NeonClient, UserType

# Initialize the client
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    environment="production"  # or "trial"
)

# Get accounts (user_type is required)
accounts = client.accounts.list(page_size=50, user_type=UserType.INDIVIDUAL)
for account in accounts:
    print(f"{account.firstName} {account.lastName}")

# Get company accounts
companies = client.accounts.list(page_size=50, user_type=UserType.COMPANY)
for company in companies:
    print(f"{company.companyName}")

# Search for accounts by email
search_results = client.accounts.search({
    "searchFields": [
        {"field": "Email 1", "operator": "EQUAL", "value": "john@example.com"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"]
})

# Search by custom field (e.g., custom field ID 123 for "Volunteer Interests")
custom_search = client.accounts.search({
    "searchFields": [
        {"field": 123, "operator": "NOT_BLANK"}  # Custom field ID as integer
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", 123]  # Include custom field in output
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

## Async Usage

```python
import asyncio
from neon_crm import AsyncNeonClient, UserType

async def main():
    async with AsyncNeonClient(
        org_id="your_org_id",
        api_key="your_api_key"
    ) as client:
        accounts = await client.accounts.list(page_size=50, user_type=UserType.INDIVIDUAL)
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

### Account Validation

The `client.accounts.list()` method requires a `user_type` parameter:

```python
from neon_crm import NeonClient, UserType

# ✅ Correct - specify user type (recommended: use enum)
individual_accounts = client.accounts.list(user_type=UserType.INDIVIDUAL)
company_accounts = client.accounts.list(user_type=UserType.COMPANY)

# ✅ Also valid - string values (backward compatible)
individual_accounts = client.accounts.list(user_type="INDIVIDUAL")
company_accounts = client.accounts.list(user_type="COMPANY")

# ❌ Will raise ValueError
accounts = client.accounts.list()  # Missing required user_type

# ❌ Will raise ValueError
accounts = client.accounts.list(user_type="invalid")  # Invalid value
```

**Valid user_type values:**
- `UserType.INDIVIDUAL` or `"INDIVIDUAL"` - Individual/person accounts
- `UserType.COMPANY` or `"COMPANY"` - Organization/company accounts

**Type Safety**: Using the `UserType` enum provides better IDE support, autocomplete, and type checking compared to string literals.

The SDK validates these parameters client-side before making API requests, providing immediate feedback for invalid values.

### Custom Fields

The SDK provides full support for searching by and retrieving custom field values. Custom fields are referenced by their integer ID.

#### Finding Custom Fields

```python
# List all custom fields for accounts
custom_fields = list(client.accounts.list_custom_fields())
for field in custom_fields:
    print(f"ID: {field['id']}, Name: {field['name']}, Type: {field['fieldType']}")

# Find a specific custom field by name
volunteer_field = client.accounts.find_custom_field_by_name('Volunteer Interests')
if volunteer_field:
    field_id = volunteer_field['id']
    print(f"'Volunteer Interests' field has ID: {field_id}")
```

#### Searching by Custom Fields

```python
# Search accounts with non-blank values in a custom field
search_request = {
    "searchFields": [
        {
            "field": 123,  # Custom field ID (integer)
            "operator": "NOT_BLANK"
        }
    ],
    "outputFields": ["Account ID", "First Name", "Last Name"]
}

results = client.accounts.search(search_request)
for account in results:
    print(f"Account {account['Account ID']}: {account['First Name']} {account['Last Name']}")

# Search for specific custom field values
search_request = {
    "searchFields": [
        {
            "field": 123,  # Custom field ID
            "operator": "EQUAL",
            "value": "Volunteer"  # Value to match
        }
    ],
    "outputFields": ["Account ID", "First Name", "Last Name"]
}
```

#### Including Custom Fields in Search Output

```python
# Include custom field values in search results
search_request = {
    "searchFields": [
        {
            "field": 123,  # Search by custom field ID
            "operator": "NOT_BLANK"
        }
    ],
    "outputFields": [
        "Account ID",
        "First Name",
        "Last Name",
        123  # Include custom field value in output (integer ID)
    ]
}

results = client.accounts.search(search_request)
for account in results:
    # Custom field values are returned using the field's display name as the key
    custom_value = account.get('Volunteer Interests', 'N/A')
    print(f"Account {account['Account ID']}: {account['First Name']} {account['Last Name']}")
    print(f"  Volunteer Interests: {custom_value}")
```

#### Multiple Custom Fields

```python
# Search by multiple custom fields
search_request = {
    "searchFields": [
        {"field": 123, "operator": "NOT_BLANK"},  # Volunteer Interests
        {"field": 456, "operator": "EQUAL", "value": "Yes"}  # Newsletter Subscription
    ],
    "outputFields": [
        "Account ID",
        "First Name",
        "Last Name",
        123,  # Volunteer Interests
        456   # Newsletter Subscription
    ]
}

results = client.accounts.search(search_request)
for account in results:
    print(f"Account {account['Account ID']}: {account['First Name']} {account['Last Name']}")
    print(f"  Volunteer Interests: {account.get('Volunteer Interests', 'N/A')}")
    print(f"  Newsletter: {account.get('Newsletter Subscription', 'N/A')}")
```

#### Working with Custom Field Names

```python
# Helper function to get field ID by name
def get_custom_field_id(client, field_name):
    field = client.accounts.find_custom_field_by_name(field_name)
    return field['id'] if field else None

# Use field names in your code, convert to IDs automatically
field_mapping = {
    'Volunteer Interests': get_custom_field_id(client, 'Volunteer Interests'),
    'Newsletter Subscription': get_custom_field_id(client, 'Newsletter Subscription'),
    'Preferred Contact Method': get_custom_field_id(client, 'Preferred Contact Method')
}

# Build search with mapped IDs
search_request = {
    "searchFields": [
        {
            "field": field_mapping['Volunteer Interests'],
            "operator": "CONTAIN",
            "value": "fundraising"
        }
    ],
    "outputFields": [
        "Account ID",
        "First Name",
        "Last Name",
        field_mapping['Volunteer Interests'],
        field_mapping['Preferred Contact Method']
    ]
}
```

**Key Points:**
- **Search fields**: Use integer custom field ID (`123`)
- **Output fields**: Use integer custom field ID (`123`)
- **Result keys**: Custom field values are returned with the field's display name as the key
- **Validation**: The SDK automatically validates custom field IDs and formats
- **Performance**: Including custom fields in search output is much more efficient than separate API calls

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

## Rate Limiting

The SDK automatically handles rate limiting with intelligent retry logic:

### Features:
- **Automatic retries** for rate limit errors (HTTP 429)
- **Exponential backoff** with jitter to prevent thundering herd
- **Honors Retry-After headers** from the server
- **Configurable retry attempts** (default: 3)
- **Maximum delay cap** of 60 seconds

### Configuration:

```python
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    max_retries=5,  # Custom retry count
)
```

### Retry Behavior:

1. **Server-specified delays**: When the API returns a `Retry-After` header, the SDK waits that duration plus small random jitter
2. **Exponential backoff**: Without a `Retry-After` header, delays follow: 1s, 2s, 4s, 8s... (with jitter)
3. **Jitter**: Random delays prevent multiple clients from retrying simultaneously
4. **Final failure**: After exhausting all retries, raises `NeonRateLimitError`

```python
from neon_crm.exceptions import NeonRateLimitError

try:
    # This will automatically retry if rate limited
    accounts = client.accounts.list(user_type=UserType.INDIVIDUAL)
except NeonRateLimitError as e:
    print(f"Rate limit exceeded after {client.max_retries} retries")
    print(f"Wait {e.retry_after} seconds before trying again")
```

The retry logic works identically for both synchronous and asynchronous clients.

## Configuration

The SDK supports flexible configuration through multiple sources with the following priority order:

1. **Init parameters** (highest priority)
2. **Configuration file**
3. **Environment variables**
4. **Default values** (lowest priority)

### Configuration File

Create a configuration file at `~/.neon/config.json`:

```json
{
  "org_id": "your_org_id",
  "api_key": "your_api_key",
  "environment": "production",
  "api_version": "2.10",
  "timeout": 30.0,
  "max_retries": 3,
  "base_url": "https://api.neoncrm.com/v2"
}
```

```python
# Client will automatically use config file
client = NeonClient()

# Or specify a custom config file path
client = NeonClient(config_path="/path/to/your/config.json")
```

### Environment Variables

Set your credentials and configuration as environment variables:

```bash
export NEON_ORG_ID="your_org_id"
export NEON_API_KEY="your_api_key"
export NEON_ENVIRONMENT="production"  # or "trial"
export NEON_API_VERSION="2.10"
export NEON_TIMEOUT="30.0"
export NEON_MAX_RETRIES="3"
export NEON_BASE_URL="https://api.neoncrm.com/v2"
```

```python
# Client will automatically use environment variables
client = NeonClient()
```

### Init Parameters (Override Everything)

```python
client = NeonClient(
    org_id="your_org_id",  # Overrides config file and env vars
    api_key="your_api_key",
    environment="production",  # "production" or "trial"
    timeout=30.0,  # Request timeout in seconds
    max_retries=3,  # Number of retries for failed requests
    api_version="2.10",  # API version
    base_url="https://custom.api.com/v2",  # Custom base URL (optional)
    config_path="~/.neon/config.json"  # Custom config file path
)
```

### Configuration Priority Example

```python
# Example showing priority order:
# 1. Config file has: org_id="file_org", timeout=60.0
# 2. Environment variable: NEON_ORG_ID="env_org"
# 3. Init parameter: org_id="init_org"

client = NeonClient(org_id="init_org")  # org_id will be "init_org"
# timeout will be 60.0 from config file (no override)
```

### Saving Configuration

You can programmatically save configuration:

```python
from neon_crm.config import ConfigLoader

loader = ConfigLoader()
loader.save_config(
    org_id="your_org_id",
    api_key="your_api_key",
    environment="production"
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
