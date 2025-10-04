# Neon CRM Python SDK Documentation

Welcome to the comprehensive documentation for the Neon CRM Python SDK - a high-quality, type-safe SDK for the Neon CRM API v2.

## Quick Links

### Getting Started
- **[Installation](getting-started/installation.md)** - Install the SDK and set up your development environment
- **[Quick Start Guide](getting-started/quickstart.md)** - Get up and running in 5 minutes
- **[Configuration](getting-started/configuration.md)** - All configuration options and best practices

### Guides & Examples
- **[User Guide](user-guide/basic-usage.md)** - Comprehensive guide to using the SDK
- **[Code Examples](examples/basic.md)** - Practical examples for common operations
- **[Permissions & Governance](permissions.md)** - Access control and role-based permissions
- **[Notebook Governance](governance_in_notebooks.md)** - Using permissions in Jupyter notebooks

### Reference
- **[API Reference](api/client.md)** - Complete API documentation

## Features

- **Full API Coverage** - Support for all 33+ Neon CRM API resource categories
- **Type Safety** - Built with Pydantic models for complete type safety and validation
- **Async/Await** - Both synchronous and asynchronous client support
- **Automatic Pagination** - Easy iteration over paginated results
- **Advanced Search** - Comprehensive search with field validation
- **Custom Objects** - Full support for Neon's custom object framework
- **Error Handling** - Specific exception types for different error conditions
- **Rate Limiting** - Built-in retry logic with exponential backoff
- **Smart Caching** - TTL-based caching for improved performance
- **Comprehensive Logging** - Configurable logging for debugging
- **Access Control** - Built-in governance with role-based permissions
- **Modern Python** - Full support for Python 3.8+

## Quick Example

```python
from neon_crm import NeonClient, UserType

# Initialize client with environment variables or config file
client = NeonClient(
    org_id="your_org_id",
    api_key="your_api_key",
    default_role="viewer"  # Optional: role-based permissions
)

# List accounts with automatic pagination
for account in client.accounts.list(user_type=UserType.INDIVIDUAL, page_size=50):
    print(f"{account.firstName} {account.lastName}")

# Search with custom fields
results = client.accounts.search({
    "searchFields": [
        {"field": "Email 1", "operator": "EQUAL", "value": "john@example.com"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"]
})
```

## Resources

### External Links
- **[GitHub Repository](https://github.com/your-username/neon-crm-python)** - Source code and issue tracker
- **[Neon CRM API Documentation](https://developer.neoncrm.com/api/general/)** - Official API reference
- **[PyPI Package](https://pypi.org/project/neon-crm/)** - Package distribution

### Community & Support
- **[GitHub Issues](https://github.com/your-username/neon-crm-python/issues)** - Report bugs and request features
- **[Discussions](https://github.com/your-username/neon-crm-python/discussions)** - Ask questions and share ideas

## What's New

Recent improvements include:
- Smart caching for custom fields and metadata (5-10 min TTL)
- Automatic retry logic for server errors (502, 503, 504)
- Enhanced search validation with dynamic field discovery
- Comprehensive logging with performance tracking
- Role-based access control system
- Improved error messages and debugging

See the [User Guide](user-guide/basic-usage.md) for complete documentation of all features.
