# Configuration Guide

Comprehensive guide to configuring the Neon CRM SDK.

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Configuration File](#configuration-file)
- [Environment Variables](#environment-variables)
- [Direct Initialization](#direct-initialization)
- [Configuration Priority](#configuration-priority)
- [Advanced Configuration](#advanced-configuration)

## Configuration Methods

The SDK supports three configuration methods, listed in order of precedence:

1. **Direct initialization** - Parameters passed to `NeonClient()`
2. **Environment variables** - Shell environment variables
3. **Configuration file** - `~/.neon/config.json`

## Configuration File

### Location

The default configuration file location is `~/.neon/config.json`. You can specify a custom location:

```python
from neon_crm import NeonClient

client = NeonClient(config_path="/path/to/custom/config.json")
```

### Format

```json
{
  "timeout": 30.0,
  "profiles": {
    "default": {
      "org_id": "your-org-id",
      "api_key": "your-api-key",
      "environment": "production",
      "api_version": "2.10",
      "max_retries": 3
    },
    "trial": {
      "org_id": "trial-org-id",
      "api_key": "trial-api-key",
      "environment": "trial"
    },
    "development": {
      "org_id": "dev-org-id",
      "api_key": "dev-api-key",
      "environment": "production",
      "base_url": "https://custom-api.example.com/v2/"
    }
  }
}
```

### Using Profiles

```python
from neon_crm import NeonClient

# Use default profile
client = NeonClient()

# Use specific profile
client = NeonClient(profile="trial")

# Use profile from environment variable
# Set: export NEON_PROFILE="development"
client = NeonClient()
```

### Creating Configuration File

```python
import json
from pathlib import Path

config_dir = Path.home() / ".neon"
config_dir.mkdir(exist_ok=True)

config = {
    "timeout": 30.0,
    "profiles": {
        "default": {
            "org_id": "your-org-id",
            "api_key": "your-api-key",
            "environment": "production"
        }
    }
}

config_file = config_dir / "config.json"
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Configuration saved to: {config_file}")
```

## Environment Variables

### Basic Configuration

```bash
export NEON_ORG_ID="your-org-id"
export NEON_API_KEY="your-api-key"
export NEON_ENVIRONMENT="production"  # or "trial"
```

### All Available Variables

```bash
# Required
export NEON_ORG_ID="your-org-id"
export NEON_API_KEY="your-api-key"

# Optional
export NEON_ENVIRONMENT="production"          # Default: production
export NEON_API_VERSION="2.10"                # Default: 2.10
export NEON_TIMEOUT="30.0"                    # Default: 30.0 seconds
export NEON_MAX_RETRIES="3"                   # Default: 3
export NEON_BASE_URL="https://..."           # Custom API URL
export NEON_PROFILE="default"                 # Config profile to use
export NEON_LOG_LEVEL="INFO"                  # DEBUG, INFO, WARNING, ERROR
export NEON_DISABLE_FIELD_CACHE="false"       # Disable field caching

# Governance
export NEON_ENABLE_GOVERNANCE="true"          # Default: true
export NEON_DEFAULT_ROLE="viewer"             # Default: viewer
```

### Using .env Files

```bash
# .env file
NEON_ORG_ID=your-org-id
NEON_API_KEY=your-api-key
NEON_ENVIRONMENT=production
```

```python
from dotenv import load_dotenv
from neon_crm import NeonClient

load_dotenv()  # Load .env file
client = NeonClient()
```

## Direct Initialization

### Basic Initialization

```python
from neon_crm import NeonClient

client = NeonClient(
    org_id="your-org-id",
    api_key="your-api-key"
)
```

### Full Configuration

```python
from neon_crm import NeonClient

client = NeonClient(
    org_id="your-org-id",
    api_key="your-api-key",
    environment="production",      # or "trial"
    api_version="2.10",
    timeout=30.0,
    max_retries=3,
    base_url=None,                # Custom API URL (optional)
    config_path=None,             # Custom config file path
    log_level="INFO",             # DEBUG, INFO, WARNING, ERROR
    enable_caching=True,          # Cache custom fields, etc.
    enable_field_cache=True,      # Cache field discovery
    default_role="viewer",        # Governance role
    enable_governance=True        # Enable access control
)
```

## Configuration Priority

When the same setting is provided through multiple methods, the SDK uses this priority order (highest to lowest):

1. **Direct initialization parameters**
2. **Environment variables**
3. **Configuration file**
4. **Default values**

### Example

```python
# Config file has: org_id="config-org"
# Environment has: NEON_ORG_ID="env-org"
# Direct parameter: org_id="direct-org"

client = NeonClient(org_id="direct-org")
# Result: Uses "direct-org" (highest priority)

client = NeonClient()
# Result: Uses "env-org" (env vars override config file)
```

## Advanced Configuration

### Logging Configuration

```python
from neon_crm import NeonClient, NeonLogger

# Set log level globally
NeonLogger.set_level_from_string("DEBUG")

# Or via client initialization
client = NeonClient(log_level="DEBUG")
```

### Custom Timeout and Retries

```python
from neon_crm import NeonClient

# Longer timeout for slow operations
client = NeonClient(
    timeout=60.0,          # 60 seconds
    max_retries=5          # 5 retry attempts
)
```

### Field Caching

The SDK caches field discoveries to improve performance:

```python
# Disable field caching
client = NeonClient(enable_field_cache=False)

# Or via environment variable
export NEON_DISABLE_FIELD_CACHE="true"

# Clear caches programmatically
client._field_caches.clear()
```

### Custom Base URL

For testing or custom deployments:

```python
client = NeonClient(
    org_id="test-org",
    api_key="test-key",
    base_url="https://custom-api.example.com/v2/"
)
```

### Governance Configuration

See the [Permissions Guide](../permissions.md) for detailed governance configuration.

```python
from neon_crm import NeonClient
from neon_crm.governance import Role, ResourceType, Permission

# Simple role-based
client = NeonClient(default_role="fundraiser")

# With overrides
client = NeonClient(
    default_role="viewer",
    permission_overrides={
        ResourceType.DONATIONS: {Permission.READ, Permission.WRITE}
    }
)

# Disable governance (not recommended for production)
client = NeonClient(enable_governance=False)
```

## Validation

The SDK validates configuration on initialization:

```python
from neon_crm import NeonClient
from neon_crm.exceptions import ConfigurationError

try:
    client = NeonClient()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Check that org_id and api_key are set
```

### Required Settings

- `org_id`: Your Neon organization ID
- `api_key`: Your API key

### Optional Settings

All other settings have sensible defaults and are optional.

## Security Best Practices

### 1. Never Commit Credentials

Add to `.gitignore`:

```gitignore
.env
.neon/
config.json
**/config.json
```

### 2. Use Environment Variables in Production

```bash
# Production deployment
export NEON_ORG_ID="${PRODUCTION_ORG_ID}"
export NEON_API_KEY="${PRODUCTION_API_KEY}"
export NEON_ENVIRONMENT="production"
```

### 3. Restrict File Permissions

```bash
chmod 600 ~/.neon/config.json
```

### 4. Use Profiles for Different Environments

```python
# Development
client = NeonClient(profile="development")

# Staging
client = NeonClient(profile="staging")

# Production
client = NeonClient(profile="production")
```

### 5. Enable Governance in Production

```python
# Production - governance enabled
client = NeonClient(
    default_role="fundraiser",
    enable_governance=True
)

# Development - governance optional
client = NeonClient(enable_governance=False)
```

## Troubleshooting

### Missing Configuration

```python
# Error: "org_id is required"
# Solution: Set via environment variable, config file, or direct parameter
export NEON_ORG_ID="your-org-id"
```

### Profile Not Found

```python
# Error: "Profile 'production' not found"
# Solution: Check ~/.neon/config.json has the profile defined
```

### Configuration File Not Found

```python
# This is OK - SDK falls back to environment variables
client = NeonClient()  # Uses env vars if config file missing
```

### Permission Denied

```bash
# Error: "Permission denied: ~/.neon/config.json"
# Solution: Fix file permissions
chmod 600 ~/.neon/config.json
```

## Examples

### Example 1: Development Setup

```python
# ~/.neon/config.json
{
  "profiles": {
    "development": {
      "org_id": "dev-org",
      "api_key": "dev-key",
      "environment": "production"
    }
  }
}

# app.py
from neon_crm import NeonClient

client = NeonClient(
    profile="development",
    log_level="DEBUG"
)
```

### Example 2: Production Deployment

```bash
# Environment variables (from secrets manager)
export NEON_ORG_ID="${SECRET_ORG_ID}"
export NEON_API_KEY="${SECRET_API_KEY}"
export NEON_ENVIRONMENT="production"
export NEON_LOG_LEVEL="WARNING"
export NEON_DEFAULT_ROLE="fundraiser"
```

```python
# app.py
from neon_crm import NeonClient

# Uses environment variables
client = NeonClient()
```

### Example 3: Testing Configuration

```python
# test_config.py
from neon_crm import NeonClient

# Override with test credentials
client = NeonClient(
    org_id="test-org",
    api_key="test-key",
    environment="trial",
    enable_governance=False,  # Disable for testing
    log_level="DEBUG"
)
```

## Next Steps

- Learn about [Basic Usage](../user-guide/basic-usage.md)
- Configure [Permissions](../permissions.md)
- See [Examples](../examples/basic.md)
