# Neon CRM Python SDK

A comprehensive, high-quality Python SDK for the Neon CRM API v2.

## Features

- **Full API Coverage**: Support for all 33+ Neon CRM API resource categories
- **Type Safety**: Built with Pydantic models for full type safety and validation
- **Async/Await Support**: Both synchronous and asynchronous clients
- **Automatic Pagination**: Easy iteration over paginated results
- **Advanced Search**: Comprehensive search capabilities with field validation
- **Custom Objects**: Full support for Neon's custom object framework
- **Error Handling**: Comprehensive error handling with specific exception types
- **Rate Limiting**: Built-in rate limit handling and retries
- **Smart Caching**: Intelligent caching system for improved performance
- **Comprehensive Logging**: Configurable logging for debugging and monitoring
- **Server Error Retry**: Automatic retry logic for server errors (502, 503, 504)
- **Access Control**: Built-in governance system with role-based permissions
- **Modern Python**: Supports Python 3.8+

## Installation

```bash
pip install neon-crm
```

For development installation, see [Development Setup](docs/getting-started/installation.md).

## Quick Start

```python
from neon_crm import NeonClient, UserType

# Initialize the client with environment variables or config file
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key"
)

# List accounts
accounts = client.accounts.list(user_type=UserType.INDIVIDUAL, page_size=10)
for account in accounts:
    print(f"{account.firstName} {account.lastName}")

# Search for accounts
results = client.accounts.search({
    "searchFields": [
        {"field": "Email 1", "operator": "EQUAL", "value": "john@example.com"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"]
})
```

**→ See [Quick Start Guide](docs/getting-started/quickstart.md) for more examples**

## Access Control & Governance

The SDK includes a comprehensive governance system for controlling user access to resources:

```python
# Create a client with viewer (read-only) permissions
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"  # or 'editor', 'admin', 'fundraiser', etc.
)

# All operations are automatically checked
accounts = list(client.accounts.list())  # ✓ Allowed
# client.accounts.create({...})          # ✗ Blocked - viewers can't create
```

**Available Roles**: `viewer`, `editor`, `admin`, `fundraiser`, `event_manager`, `volunteer_coordinator`

**→ See [Permissions Documentation](docs/permissions.md) for complete details**

## Configuration

The SDK supports multiple configuration methods with priority order:

1. **Init parameters** (highest priority)
2. **Configuration file** (`~/.neon/config.json`)
3. **Environment variables**
4. **Default values** (lowest priority)

### Environment Variables

```bash
export NEON_ORG_ID="your_org_id"
export NEON_API_KEY="your_api_key"
export NEON_ENVIRONMENT="production"  # or "trial"
export NEON_DEFAULT_ROLE="viewer"     # optional
```

### Configuration File

Create `~/.neon/config.json`:

```json
{
  "org_id": "your_org_id",
  "api_key": "your_api_key",
  "environment": "production"
}
```

**→ See [Configuration Guide](docs/getting-started/configuration.md) for all options**

## Documentation

- **[Quick Start Guide](docs/getting-started/quickstart.md)** - Get started in 5 minutes
- **[Configuration](docs/getting-started/configuration.md)** - All configuration options
- **[Code Examples](docs/examples/basic.md)** - Practical code examples
- **[User Guide](docs/user-guide/basic-usage.md)** - Comprehensive usage guide
- **[Permissions & Governance](docs/permissions.md)** - Access control system
- **[API Reference](docs/api/client.md)** - API documentation

## API Resources

The SDK provides access to all Neon CRM API resources:

- **Accounts** - Contact and organization management
- **Donations** - Donation tracking and management
- **Events** - Event management
- **Memberships** - Membership management
- **Activities** - Activity tracking
- **Custom Objects** - Custom object framework
- **Volunteers** - Volunteer management
- **Campaigns** - Campaign management
- **And 25+ more resources**

## Error Handling

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
    print("Rate limit exceeded")
except NeonAPIError as e:
    print(f"API error: {e.message}")
```

**→ See [User Guide](docs/user-guide/basic-usage.md#error-handling) for comprehensive error handling**

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
# Run all tests
pytest

# Run specific test file
pytest tests/test_accounts.py

# Run with coverage
pytest --cov=neon_crm
```

### Using Just (Optional)

This project includes both `Makefile` and `justfile` for build automation:

```bash
# Install just: brew install just

# List all commands
just

# Common commands
just test              # Run tests
just setup-dev         # Set up dev environment
just test-notebooks    # Test Jupyter notebooks
```

## Recent Improvements

### Performance & Reliability
- **Smart Caching**: TTL-based caching for custom fields and metadata (5-10 min TTL)
- **Server Error Retry**: Automatic retry for 502/503/504 errors with exponential backoff
- **Comprehensive Logging**: Configurable logging with performance tracking
- **Enhanced Validation**: Improved custom field support with dynamic validation

### Developer Experience
- **Test Coverage**: 68% overall, 80%+ in core modules
- **Better Debugging**: Detailed logging with request/response monitoring
- **Improved Errors**: More helpful validation error messages
- **Documentation**: MkDocs-based framework for maintainable docs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [Full documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/neon-crm-python/issues)
- **Neon CRM API**: [Official API Documentation](https://developer.neoncrm.com/api/general/)
