# Configuration Profiles

The Neon CRM SDK supports configuration profiles, allowing you to manage multiple environments (production, sandbox, trial, etc.) from a single configuration file.

## Configuration File Structure

Create a config file at `~/.neon/config.json`:

### Basic Profile Configuration

```json
{
  "profiles": {
    "prod": {
      "org_id": "your_prod_org_id",
      "api_key": "your_prod_api_key",
      "environment": "production"
    },
    "sandbox": {
      "org_id": "your_sandbox_org_id",
      "api_key": "your_sandbox_api_key",
      "environment": "production"
    },
    "trial": {
      "org_id": "your_trial_org_id",
      "api_key": "your_trial_api_key",
      "environment": "trial"
    }
  }
}
```

### Profile with Shared Defaults

```json
{
  "api_version": "2.10",
  "timeout": 30.0,
  "max_retries": 3,
  "profiles": {
    "prod": {
      "org_id": "your_prod_org_id",
      "api_key": "your_prod_api_key",
      "environment": "production"
    },
    "sandbox": {
      "org_id": "your_sandbox_org_id",
      "api_key": "your_sandbox_api_key",
      "environment": "production",
      "timeout": 60.0
    }
  }
}
```

## Using Profiles

### In Python Code

```python
from neon_crm import NeonClient

# Use a specific profile
prod_client = NeonClient(profile="prod")
sandbox_client = NeonClient(profile="sandbox")
trial_client = NeonClient(profile="trial")

# Use default profile (or "default" profile if defined)
default_client = NeonClient()

# Profile can be overridden by explicit parameters
client = NeonClient(profile="prod", timeout=60.0)
```

### With Environment Variables

```bash
# Set profile via environment variable
export NEON_PROFILE=sandbox
python your_script.py

# Override specific settings
export NEON_PROFILE=prod
export NEON_TIMEOUT=60
python your_script.py
```

### In Tests

The SDK provides profile-aware test fixtures:

```python
def test_with_sandbox(sandbox_client):
    """Uses sandbox profile automatically."""
    accounts = list(sandbox_client.accounts.list(limit=5))
    assert len(accounts) <= 5

def test_with_production_readonly(production_client):
    """Uses prod profile - read-only operations only!"""
    accounts = list(production_client.accounts.list(limit=1))
    assert len(accounts) <= 1
```

## Configuration Priority

The configuration loading follows this priority order:

1. **Explicit parameters** in code: `NeonClient(org_id="...")`
2. **Profile configuration** from `~/.neon/config.json`
3. **Environment variables**: `NEON_ORG_ID`, `NEON_API_KEY`, etc.
4. **Default values**

## Profile Management

### Creating Profiles Programmatically

```python
from neon_crm.config import ConfigLoader

config = ConfigLoader()

# Save a new profile
config.save_config(
    profile="new_env",
    org_id="new_org_id",
    api_key="new_api_key",
    environment="production"
)

# List all profiles
profiles = config.list_profiles()
print(f"Available profiles: {profiles}")

# Delete a profile
config.delete_profile("old_env")
```

## Environment-Specific Usage

### Production Environment

```python
# For production - read operations only
prod_client = NeonClient(profile="prod")
accounts = list(prod_client.accounts.list(limit=10))
```

### Sandbox Environment

```python
# For sandbox - safe for testing
sandbox_client = NeonClient(profile="sandbox")

# Safe to test write operations
new_account = sandbox_client.accounts.create({
    "individualAccount": {
        "firstName": "Test",
        "lastName": "User",
        "email": "test@example.com"
    }
})
```

### Trial Environment

```python
# For trial instance
trial_client = NeonClient(profile="trial")

# Trial instances use different base URL automatically
print(trial_client.base_url)  # https://trial.neoncrm.com/v2/
```

## Best Practices

1. **Use profiles for different environments** - separate prod, sandbox, trial
2. **Never commit API keys** - use environment variables in CI/CD
3. **Use sandbox for development** - safe for write operations
4. **Use trial for demos** - temporary test data
5. **Set appropriate timeouts** - production may need longer timeouts
6. **Profile naming** - use consistent names like `prod`, `sandbox`, `dev`

## Common Profile Setup

```json
{
  "timeout": 30.0,
  "max_retries": 3,
  "api_version": "2.10",
  "profiles": {
    "prod": {
      "org_id": "prod_org_123",
      "api_key": "prod_key_abc",
      "environment": "production",
      "timeout": 60.0
    },
    "sandbox": {
      "org_id": "sandbox_org_456",
      "api_key": "sandbox_key_def",
      "environment": "production"
    },
    "trial": {
      "org_id": "trial_org_789",
      "api_key": "trial_key_ghi",
      "environment": "trial"
    },
    "dev": {
      "org_id": "dev_org_000",
      "api_key": "dev_key_zzz",
      "environment": "trial",
      "timeout": 10.0
    }
  }
}
```

This setup provides:
- **prod**: Production environment with longer timeout
- **sandbox**: Sandbox environment with standard settings
- **trial**: Trial instance for demos
- **dev**: Development environment with shorter timeout for faster feedback
