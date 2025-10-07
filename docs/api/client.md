# Client API Reference

The main client classes for interacting with the Neon CRM API.

!!! tip "Interactive API Explorer"
    For a complete interactive API reference with the ability to test endpoints, see the [Interactive API Reference](interactive.md).

## NeonClient

::: neon_crm.client.NeonClient
    options:
      show_source: false
      show_signature_annotations: true
      docstring_style: google

## AsyncNeonClient

::: neon_crm.client.AsyncNeonClient
    options:
      show_source: false
      show_signature_annotations: true
      docstring_style: google

## Configuration

The client can be configured through multiple sources with the following priority order:

1. **Init parameters** (highest priority)
2. **Configuration file** (`~/.neon/config.json`)
3. **Environment variables**
4. **Default values** (lowest priority)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEON_ORG_ID` | Your Neon organization ID | Required |
| `NEON_API_KEY` | Your API key | Required |
| `NEON_ENVIRONMENT` | API environment (`production` or `trial`) | `production` |
| `NEON_API_VERSION` | API version to use | `2.10` |
| `NEON_TIMEOUT` | Request timeout in seconds | `30.0` |
| `NEON_MAX_RETRIES` | Number of retries for failed requests | `3` |
| `NEON_BASE_URL` | Custom base URL | Auto-determined |
| `NEON_LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

Create `~/.neon/config.json`:

```json
{
  "org_id": "your_org_id",
  "api_key": "your_api_key",
  "environment": "production",
  "api_version": "2.10",
  "timeout": 30.0,
  "max_retries": 3,
  "profiles": {
    "prod": {
      "org_id": "prod_org_id",
      "api_key": "prod_api_key",
      "environment": "production"
    },
    "sandbox": {
      "org_id": "sandbox_org_id",
      "api_key": "sandbox_api_key",
      "environment": "trial"
    }
  }
}
```

## Features

### Caching

The client includes optional caching for expensive operations:

- Custom field lookups
- Search field definitions
- Output field definitions
- Custom object metadata

```python
# Enable caching (default)
client = NeonClient(enable_caching=True)

# Disable caching
client = NeonClient(enable_caching=False)

# Clear cache
client.clear_cache()

# Get cache statistics
stats = client.get_cache_stats()
print(stats)  # {'custom_fields': 15, 'search_fields': 8, ...}
```

### Logging

Configurable logging with performance tracking:

```python
# Set log level via parameter
client = NeonClient(log_level="DEBUG")

# Or via environment variable
import os
os.environ["NEON_LOG_LEVEL"] = "INFO"
client = NeonClient()
```

### Retry Logic

Automatic retries for:
- Rate limits (429) with exponential backoff
- Network errors (connection, timeout)
- Server errors (502, 503, 504)

```python
# Configure retry behavior
client = NeonClient(max_retries=5, timeout=60.0)
```
