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
- **Caching**: Optional caching for custom fields and search metadata
- **Logging**: Configurable logging with performance tracking
- **Modern Python**: Supports Python 3.8+

## Quick Example

```python
from neon_crm import NeonClient, UserType

# Initialize the client
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key"
)

# Get individual accounts
for account in client.accounts.list(user_type=UserType.INDIVIDUAL):
    print(f"{account.firstName} {account.lastName}")

# Search with custom fields
search_results = client.accounts.search({
    "searchFields": [
        {"field": 123, "operator": "NOT_BLANK"}  # Custom field ID
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", 123]
})

for result in search_results:
    print(f"Account {result['Account ID']}: {result.get('Custom Field Name', 'N/A')}")
```

## Getting Started

1. [Installation](getting-started/installation.md) - Install the SDK
2. [Quick Start](getting-started/quickstart.md) - Basic usage examples
3. [Configuration](getting-started/configuration.md) - Configuration options

## Resources

- [API Reference](api/client.md) - Complete API documentation
- [Examples](examples/basic.md) - Working code examples
- [GitHub Repository](https://github.com/your-username/neon-crm-python)
- [Neon CRM API Documentation](https://developer.neoncrm.com/api/general/)

## Support

Need help? Check out:

- [User Guide](user-guide/basic-usage.md) for detailed usage instructions
- [Examples](examples/basic.md) for working code samples
- [API Reference](api/client.md) for complete documentation
- [GitHub Issues](https://github.com/your-username/neon-crm-python/issues) for bug reports and feature requests
