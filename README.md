# Neon CRM Python SDK

A comprehensive, high-quality Python SDK for the Neon CRM API v2.

## Features

- **Full API Coverage**: Support for all 33+ Neon CRM API resource categories
- **Type Safety**: Built with Pydantic models for full type safety and validation
- **Async/Await Support**: Both synchronous and asynchronous clients
- **Automatic Pagination**: Easy iteration over paginated results
- **Advanced Search**: Support for Neon's flexible search capabilities with comprehensive validation
- **Custom Objects**: Full support for Neon's custom object framework
- **Error Handling**: Comprehensive error handling with specific exception types
- **Rate Limiting**: Built-in rate limit handling and retries
- **Smart Caching**: Intelligent caching system for improved performance
- **Comprehensive Logging**: Configurable logging for debugging and monitoring
- **Server Error Retry**: Automatic retry logic for server errors (502, 503, 504)
- **Access Control**: Built-in governance system with role-based permissions
- **Modern Python**: Supports Python 3.8+

## Recent Improvements

### Performance & Reliability Enhancements
- **🚀 Smart Caching**: TTL-based caching for custom fields and search metadata (5-10 minute TTL) - significantly improves performance for repeated operations
- **🔧 Comprehensive Logging**: Configurable logging with `NEON_LOG_LEVEL` environment variable support for debugging and monitoring
- **🛡️ Server Error Retry**: Automatic retry logic for server errors (502, 503, 504) with exponential backoff
- **✅ Enhanced Search Validation**: Improved custom field support with dynamic field validation and better error messages
- **🔍 Fuzzy & Semantic Search**: Find fields even with typos or related terms (e.g., "address" finds "location")
- **📚 Documentation Framework**: MkDocs integration for maintainable, searchable documentation

### Developer Experience
- **🧪 Comprehensive Test Coverage**: 68% overall coverage with 80%+ in core modules for improved reliability
- **⚡ Performance Optimization**: Caching reduces API load and improves response times for custom field operations
- **🐛 Better Debugging**: Detailed logging with performance tracking and request/response monitoring
- **🔍 Improved Error Messages**: More helpful validation errors for search operations and custom fields

These improvements make the SDK more reliable, performant, and easier to debug in production environments.

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

## Access Control & Governance

The SDK includes a comprehensive governance system for controlling user access to different resources and actions.

### Simple Role-Based Setup (Recommended)

```python
# Create a client with viewer (read-only) permissions
# Governance is enabled by default
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"  # or 'editor', 'admin', 'fundraiser', etc.
)

# All operations are automatically checked against viewer permissions
accounts = list(client.accounts.list())  # ✓ Allowed - viewers can read
# client.accounts.create({...})          # ✗ Blocked - viewers can't create
```

### Environment Variable Configuration

```bash
# .env file
NEON_DEFAULT_ROLE=editor
```

```python
# Automatically uses role from .env
client = NeonClient()
```

### Available Roles
- **viewer** - Read-only access to most resources
- **editor** - Read and write access to most resources
- **admin** - Full access to all resources
- **fundraiser** - Full access to donation-related activities
- **event_manager** - Full control over events and registrations
- **volunteer_coordinator** - Manage volunteers and activities

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

**📚 See [docs/permissions.md](docs/permissions.md) for complete documentation, advanced usage, and best practices.**

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

## Smart Caching

The SDK includes an intelligent caching system to improve performance and reduce API load:

### Features:
- **TTL-based caching** with automatic expiration (5 minutes for custom fields, 10 minutes for search metadata)
- **Thread-safe operation** for concurrent usage
- **Automatic cleanup** of expired entries
- **Performance optimization** for expensive lookups like custom field metadata
- **Configurable caching** - can be disabled if needed

### Configuration:

```python
# Enable caching (default: True)
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    enable_caching=True
)

# Disable caching if needed
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    enable_caching=False
)
```

### What Gets Cached:
- **Custom field metadata**: Field definitions, names, types (5-minute TTL)
- **Search and output fields**: Valid field names for search operations (10-minute TTL)
- **Resource metadata**: Field validation data for improved search performance

The caching system significantly improves performance for applications that frequently work with custom fields or perform multiple search operations.

## Comprehensive Logging

The SDK provides extensive logging capabilities for debugging and monitoring:

### Features:
- **Configurable log levels** via environment variable or programmatic setting
- **Performance tracking** for API calls and operations
- **Detailed request/response logging** for debugging
- **Separate test logger** for development
- **Thread-safe operation** with logger caching

### Configuration:

```python
# Set log level via environment variable
export NEON_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Or configure programmatically
import logging
from neon_crm.logging import NeonLogger

logger = NeonLogger.get_logger("my_app")
logger.set_level_from_string("DEBUG")
```

### Usage Examples:

```python
from neon_crm.logging import NeonLogger

# Get a logger for your application
logger = NeonLogger.get_logger("my_app")

# Use standard logging methods
logger.info("Starting account sync")
logger.debug(f"Processing account {account_id}")
logger.error("Failed to sync account", exc_info=True)

# For tests (separate logger to avoid interference)
test_logger = NeonLogger.get_test_logger("test_accounts")
```

### What Gets Logged:
- **API requests and responses** with timing information
- **Cache hits and misses** for performance monitoring
- **Validation operations** and field lookups
- **Error conditions** with full context
- **Performance metrics** for optimization

## Server Error Retry Logic

The SDK automatically handles server errors with intelligent retry logic:

### Features:
- **Automatic retries** for server errors (502, 503, 504) and rate limits (429)
- **Exponential backoff** with jitter to prevent thundering herd
- **Honors Retry-After headers** from the server
- **Configurable retry attempts** (default: 3)
- **Maximum delay cap** of 60 seconds

### Server Error Handling:
The SDK now automatically retries failed requests due to temporary server issues:

```python
from neon_crm.exceptions import NeonServerError, NeonRateLimitError

try:
    # This will automatically retry server errors (502, 503, 504)
    accounts = client.accounts.list(user_type=UserType.INDIVIDUAL)
except NeonServerError as e:
    print(f"Server error after {client.max_retries} retries: {e}")
except NeonRateLimitError as e:
    print(f"Rate limit exceeded: wait {e.retry_after} seconds")
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

## Enhanced Search Validation

The SDK now includes comprehensive search validation with improved custom field support:

### Features:
- **Dynamic field validation** with automatic API discovery
- **Custom field support** with integer ID validation
- **Operator compatibility checking** for different field types
- **Performance optimization** through field metadata caching
- **Comprehensive error messages** for invalid search requests

### Custom Field Integration:
```python
# Find custom fields by name
volunteer_field = client.accounts.find_custom_field_by_name('Volunteer Interests')
field_id = volunteer_field['id'] if volunteer_field else None

# Use in search with automatic validation
if field_id:
    search_request = {
        "searchFields": [
            {"field": field_id, "operator": "NOT_BLANK"}
        ],
        "outputFields": ["Account ID", "First Name", "Last Name", field_id]
    }
    results = client.accounts.search(search_request)
```

### Validation Improvements:
- **Field existence checking** against live API metadata
- **Operator validation** based on field types and capabilities
- **Value format validation** for different operators (IN_RANGE, etc.)
- **Output field validation** to prevent API errors
- **Custom field ID validation** with helpful error messages

## Documentation Framework

The SDK now uses MkDocs for comprehensive, maintainable documentation:

### Features:
- **Automatic API documentation** generated from docstrings
- **Material Design theme** for professional appearance
- **Easy maintenance** with markdown files
- **Searchable documentation** with built-in search
- **Mobile-responsive design** for all devices

### Building Documentation:
```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

The documentation framework ensures that SDK improvements are automatically reflected in user-facing documentation without manual maintenance.

## Fuzzy & Semantic Field Search

The SDK includes powerful fuzzy and semantic search capabilities to help find fields even when you don't know the exact name or have typos.

### Features:
- **Fuzzy Matching**: Find fields with typos, abbreviations, or partial names
- **Semantic Search**: Find conceptually related fields (e.g., "address" finds "location", "residence")
- **Combined Search**: Automatically combines both fuzzy and semantic results
- **Helpful Suggestions**: Get suggestions when field lookups fail
- **Performance Optimized**: Efficient algorithms for large field lists

### Custom Field Fuzzy Search

```python
from neon_crm import NeonClient

client = NeonClient(org_id="your_org", api_key="your_key")

# Basic fuzzy search - finds fields with similar names
results = client.custom_fields.fuzzy_search_by_name("volunter")  # Note the typo
for field, score in results:
    print(f"{field['name']} (ID: {field['id']}) - Score: {score:.2f}")
# Output: "Volunteer Interests (ID: 123) - Score: 0.85"

# Semantic search - finds conceptually related fields
results = client.custom_fields.semantic_search_by_name("address")
for field, score in results:
    print(f"{field['name']} (ID: {field['id']}) - Score: {score:.2f}")
# Output: "Home Location (ID: 124) - Score: 0.75"
#         "Residence Info (ID: 125) - Score: 0.65"

# Get suggestions when field not found
result = client.custom_fields.find_with_suggestions("volunter", "Account")
if result['found']:
    field = result['field']
    print(f"Found: {field['name']}")
else:
    print("Field not found. Did you mean:")
    for suggestion in result['fuzzy_suggestions']:
        print(f"  - {suggestion}")
    print("Or perhaps you meant:")
    for suggestion in result['semantic_suggestions']:
        print(f"  - {suggestion}")
```

### Standard Field Fuzzy Search

```python
# Search for standard API fields with fuzzy matching
results = client.accounts.fuzzy_search_fields("frist_name")  # Note the typo
for field_name, score, match_type in results:
    print(f"{field_name} - Score: {score:.2f} ({match_type})")
# Output: "first_name - Score: 0.90 (fuzzy)"

# Get suggestions for invalid field names
suggestions = client.accounts.suggest_field_corrections("emaill")
if suggestions['fuzzy_suggestions']:
    print("Did you mean:")
    for suggestion in suggestions['fuzzy_suggestions']:
        print(f"  - {suggestion}")
# Output: "email_address", "email_1", "email_2"

if suggestions['semantic_suggestions']:
    print("Or perhaps you meant:")
    for suggestion in suggestions['semantic_suggestions']:
        print(f"  - {suggestion}")
# Output: "contact_email", "electronic_mail"
```

### Field Lookup with Automatic Suggestions

The SDK can automatically provide helpful suggestions when field lookups fail:

```python
from neon_crm.resources.custom_fields import FieldNotFoundError

try:
    # This will raise an exception with suggestions if field not found
    field = client.custom_fields.find_by_name_and_category(
        "volunter", "Account", raise_on_not_found=True
    )
    print(f"Found field: {field['name']}")
except FieldNotFoundError as e:
    print(e)  # Automatically includes suggestions in the error message
```

Output when field not found:
```
Field 'volunter' not found in category 'Account'.

Did you mean one of these similar field names?
  - volunteer_interests
  - volunteer_hours
  - volunteer_skills

Or perhaps you're looking for one of these related fields?
  - member_activities
  - service_history
  - help_preferences
```

### Advanced Search Options

```python
# Search with custom thresholds and limits
results = client.custom_fields.fuzzy_search_by_name(
    "contact",
    category="Account",
    threshold=0.4,          # Minimum similarity score
    max_results=5,          # Limit results
    case_sensitive=False    # Case insensitive matching
)

# Combined fuzzy and semantic search
results = client.accounts.fuzzy_search_fields(
    "addr",
    field_type="search",    # 'search', 'output', or 'all'
    include_semantic=True,  # Include semantic matches
    threshold=0.3
)

# Search specific field types
search_field_results = client.accounts.fuzzy_search_fields("email", field_type="search")
output_field_results = client.accounts.fuzzy_search_fields("address", field_type="output")
all_field_results = client.accounts.fuzzy_search_fields("phone", field_type="all")
```

### Use Cases

**1. Handling User Input**: When users enter field names in forms or configuration
```python
user_field = input("Enter field name: ")  # User types "volunter"
result = client.custom_fields.find_with_suggestions(user_field, "Account")
if not result['found']:
    print("Field not found. Suggestions:")
    for suggestion in result['fuzzy_suggestions'][:3]:
        print(f"  - {suggestion}")
```

**2. Field Discovery**: Finding fields when you know the concept but not exact name
```python
# Find all address-related fields
address_fields = client.custom_fields.semantic_search_by_name("address")
location_fields = client.custom_fields.semantic_search_by_name("location")
```

**3. API Integration**: Robust field mapping in integrations
```python
def get_field_id(field_name, category):
    """Get field ID with automatic fallback to similar fields."""
    field = client.custom_fields.find_by_name_and_category(field_name, category)
    if field:
        return field['id']

    # Try fuzzy search as fallback
    results = client.custom_fields.fuzzy_search_by_name(field_name, category, threshold=0.7)
    if results:
        return results[0][0]['id']  # Return best match

    return None
```

**4. Search Request Validation**: Better error messages
```python
def validate_search_field(field_name):
    """Validate search field with helpful suggestions."""
    available_fields = client.accounts._validator._get_available_search_fields()
    if field_name not in available_fields:
        suggestions = client.accounts.suggest_field_corrections(field_name)
        if suggestions['fuzzy_suggestions']:
            raise ValueError(f"Invalid field '{field_name}'. Did you mean: {', '.join(suggestions['fuzzy_suggestions'][:3])}")
        else:
            raise ValueError(f"Invalid field '{field_name}'. No similar fields found.")
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

## Using Just (Optional)

This project includes both a `Makefile` and a `justfile`. The `justfile` provides the same commands with cleaner syntax.

### Installing Just

```bash
# macOS
brew install just

# Linux
cargo install just

# Or see: https://github.com/casey/just
```

### Using Just

```bash
# List all commands
just

# Run tests
just test

# Set up dev environment
just setup-dev

# Test notebooks
just test-notebooks

# See all commands
just --list
```

All `make` commands work identically with `just` (e.g., `make test` → `just test`).
