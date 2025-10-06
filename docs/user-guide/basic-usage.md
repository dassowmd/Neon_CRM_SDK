# User Guide: Basic Usage

Comprehensive guide to using the Neon CRM SDK.

## Table of Contents

- [Overview](#overview)
- [Client Initialization](#client-initialization)
- [Working with Resources](#working-with-resources)
- [Search Operations](#search-operations)
- [CRUD Operations](#crud-operations)
- [Custom Fields](#custom-fields)
- [Pagination](#pagination)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Overview

The Neon CRM SDK provides a Pythonic interface to the Neon CRM API. It handles authentication, pagination, error handling, and provides type hints for better development experience.

### Key Features

- **Simple Configuration**: Environment variables, config files, or direct initialization
- **Automatic Pagination**: Iterate through all results without manual page management
- **Built-in Governance**: Role-based access control for secure operations
- **Type Hints**: Full type annotations for better IDE support
- **Error Handling**: Comprehensive exception hierarchy
- **Field Discovery**: Automatic field name discovery and caching
- **Retry Logic**: Automatic retries for transient failures

## Client Initialization

### Basic Initialization

The simplest way to initialize the client is to use environment variables or a config file:

```python
from neon_crm import NeonClient

# Automatically loads from environment or ~/.neon/config.json
client = NeonClient()
```

### Configuration Options

See the [Configuration Guide](../getting-started/configuration.md) for detailed configuration options.

```python
from neon_crm import NeonClient

client = NeonClient(
    org_id="your-org-id",           # Required if not in env/config
    api_key="your-api-key",         # Required if not in env/config
    environment="production",        # or "trial"
    default_role="fundraiser",      # For governance
    enable_governance=True,         # Enable access control
    timeout=30.0,                   # Request timeout in seconds
    max_retries=3,                  # Number of retry attempts
    log_level="INFO"                # Logging level
)
```

## Working with Resources

The SDK organizes API endpoints into resource managers. Each resource provides methods for common operations.

### Available Resources

```python
client.accounts          # Account management
client.addresses         # Address management
client.donations         # Donation records
client.events            # Event management
client.memberships       # Membership records
client.campaigns         # Campaign management
client.custom_fields     # Custom field definitions
client.custom_objects    # Custom object records
client.activities        # Activity records
client.volunteers        # Volunteer records
client.pledges           # Pledge records
client.recurring_donations  # Recurring donation setup
client.webhooks          # Webhook configuration
```

### Resource Methods

Most resources provide these standard methods:

```python
# Search for records
results = client.accounts.search(search_request)

# Retrieve a specific record
record = client.accounts.retrieve(record_id)

# Create a new record
new_record = client.accounts.create(data)

# Update an existing record
updated = client.accounts.update(record_id, data)

# Delete a record
client.accounts.delete(record_id)

# Get available search fields
fields = client.accounts.get_search_fields()

# Get available output fields
fields = client.accounts.get_output_fields()
```

## Search Operations

### Basic Search

```python
search_request = {
    "searchFields": [
        {"field": "Account Type", "operator": "EQUAL", "value": "Individual"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"],
    "pagination": {"currentPage": 0, "pageSize": 50}
}

results = list(client.accounts.search(search_request))
```

### Search Operators

Common operators available for search fields:

- `EQUAL`: Exact match
- `NOT_EQUAL`: Not equal to value
- `CONTAIN`: Contains substring
- `NOT_CONTAIN`: Does not contain substring
- `BLANK`: Field is empty
- `NOT_BLANK`: Field has a value
- `GREATER_THAN`: Greater than value (numbers, dates)
- `GREATER_AND_EQUAL`: Greater than or equal
- `LESS_THAN`: Less than value
- `LESS_AND_EQUAL`: Less than or equal

### Multiple Search Criteria

```python
# All criteria must match (AND logic)
search_request = {
    "searchFields": [
        {"field": "Account Type", "operator": "EQUAL", "value": "Individual"},
        {"field": "State/Province", "operator": "EQUAL", "value": "CA"},
        {"field": "Email 1", "operator": "NOT_BLANK"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1", "City"],
    "pagination": {"currentPage": 0, "pageSize": 100}
}

ca_individuals_with_email = list(client.accounts.search(search_request))
```

### Date Range Searches

```python
from datetime import datetime, timedelta

# Donations in the last 90 days
start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

search_request = {
    "searchFields": [
        {"field": "Donation Date", "operator": "GREATER_AND_EQUAL", "value": start_date}
    ],
    "outputFields": [
        "Donation ID",
        "Account ID",
        "Donation Amount",
        "Donation Date",
        "Campaign Name"
    ],
    "pagination": {"currentPage": 0, "pageSize": 200}
}

recent_donations = list(client.donations.search(search_request))
```

### Sorting Results

```python
# Note: Sorting must be done client-side after fetching
import pandas as pd

donations = list(client.donations.search(search_request))
df = pd.DataFrame(donations)
sorted_df = df.sort_values('Donation Amount', ascending=False)
```

## CRUD Operations

### Create Operations

#### Create an Account

```python
new_account = {
    "individualAccount": {
        "accountCustomFields": [],
        "primaryContact": {
            "firstName": "John",
            "lastName": "Doe",
            "email1": "john.doe@example.com",
            "contactCustomFields": [],
            "addresses": [
                {
                    "addressType": "Home",
                    "addressLine1": "123 Main St",
                    "city": "San Francisco",
                    "stateProvince": {"code": "CA"},
                    "zipCode": "94102",
                    "country": {"name": "United States"}
                }
            ],
            "phones": [
                {"type": "Mobile", "number": "555-0123"}
            ]
        }
    }
}

result = client.accounts.create(new_account)
account_id = result['id']
print(f"Created account ID: {account_id}")
```

#### Create a Donation

```python
from datetime import datetime

new_donation = {
    "accountId": 12345,
    "amount": 250.00,
    "donationDate": datetime.now().strftime('%Y-%m-%d'),
    "campaign": {"id": 5},
    "fund": {"id": 1},
    "payments": [
        {
            "paymentStatus": "Succeeded",
            "tenderType": {"id": 1},
            "receivedDate": datetime.now().strftime('%Y-%m-%d'),
            "amount": 250.00
        }
    ]
}

result = client.donations.create(new_donation)
print(f"Created donation ID: {result['id']}")
```

### Read Operations

#### Retrieve by ID

```python
account_id = 12345
account = client.accounts.retrieve(account_id)

print(f"Name: {account['primaryContact']['firstName']} {account['primaryContact']['lastName']}")
print(f"Email: {account['primaryContact']['email1']}")
```

#### Retrieve with Error Handling

```python
from neon_crm.exceptions import NeonAPIError

try:
    account = client.accounts.retrieve(account_id)
    print(f"Found account: {account['primaryContact']['firstName']}")
except NeonAPIError as e:
    if e.status_code == 404:
        print(f"Account {account_id} not found")
    else:
        print(f"API error: {e.message}")
```

### Update Operations

#### Update Account Information

```python
account_id = 12345

update_data = {
    "individualAccount": {
        "primaryContact": {
            "email1": "newemail@example.com",
            "phones": [
                {"type": "Mobile", "number": "555-9999"}
            ]
        }
    }
}

result = client.accounts.update(account_id, update_data)
print(f"Updated account {account_id}")
```

#### Partial Updates

```python
# Only update specific fields
update_data = {
    "individualAccount": {
        "primaryContact": {
            "email1": "updated@example.com"
        }
    }
}

# This only updates the email, leaving other fields unchanged
client.accounts.update(account_id, update_data)
```

### Delete Operations

```python
account_id = 12345

try:
    client.accounts.delete(account_id)
    print(f"Deleted account {account_id}")
except NeonAPIError as e:
    print(f"Failed to delete: {e.message}")
```

## Custom Fields

### Discovering Custom Fields

```python
# Get all available custom fields for accounts
search_fields = client.accounts.get_search_fields()

# Filter for custom fields
custom_fields = [
    field for field in search_fields
    if field.get('fieldName', '').startswith('Custom - ')
]

for field in custom_fields:
    print(f"{field['fieldName']}: {field.get('fieldType', 'unknown')}")
```

### Setting Custom Field Values

```python
account_id = 12345

update_data = {
    "individualAccount": {
        "accountCustomFields": [
            {
                "id": "123",  # Custom field ID
                "name": "Custom - VIP Status",
                "value": "Gold"
            },
            {
                "id": "456",
                "name": "Custom - Last Event Date",
                "value": "2025-01-15"
            },
            {
                "id": "789",
                "name": "Custom - Lifetime Value",
                "value": "5000.00"
            }
        ]
    }
}

client.accounts.update(account_id, update_data)
```

### Searching by Custom Fields

```python
# Search for accounts with specific custom field value
search_request = {
    "searchFields": [
        {"field": "Custom - VIP Status", "operator": "EQUAL", "value": "Gold"}
    ],
    "outputFields": [
        "Account ID",
        "First Name",
        "Last Name",
        "Custom - VIP Status",
        "Custom - Lifetime Value"
    ],
    "pagination": {"currentPage": 0, "pageSize": 50}
}

vip_gold_accounts = list(client.accounts.search(search_request))
```

## Pagination

### Automatic Pagination

The SDK automatically handles pagination by default:

```python
# This fetches ALL results across all pages
all_accounts = list(client.accounts.search(search_request))
print(f"Total accounts: {len(all_accounts)}")
```

### Limiting Results

```python
from itertools import islice

# Get only first 100 results
first_100 = list(islice(client.accounts.search(search_request), 100))
```

### Manual Pagination Control

```python
page_size = 50
all_results = []

for page_num in range(10):  # Fetch first 10 pages
    search_request = {
        "searchFields": [],
        "outputFields": ["Account ID", "First Name", "Last Name"],
        "pagination": {"currentPage": page_num, "pageSize": page_size}
    }

    page_results = list(client.accounts.search(search_request))

    if not page_results:
        break  # No more results

    all_results.extend(page_results)
    print(f"Fetched page {page_num + 1}, total so far: {len(all_results)}")

print(f"Final total: {len(all_results)}")
```

### Pagination with Progress

```python
from tqdm import tqdm

search_request = {
    "searchFields": [],
    "outputFields": ["Account ID", "First Name"],
    "pagination": {"currentPage": 0, "pageSize": 200}
}

results = []
for item in tqdm(client.accounts.search(search_request), desc="Fetching accounts"):
    results.append(item)

print(f"Fetched {len(results)} accounts")
```

## Error Handling

### Exception Hierarchy

```python
from neon_crm.exceptions import (
    NeonAPIError,           # Base API error
    NeonValidationError,    # Validation failed
    ConfigurationError      # Configuration issue
)
from neon_crm.governance.access_control import PermissionError  # Governance error
```

### Comprehensive Error Handling

```python
from neon_crm.exceptions import NeonAPIError, NeonValidationError
from neon_crm.governance.access_control import PermissionError

try:
    result = client.accounts.create(new_account)
    print(f"Success: Created account {result['id']}")

except NeonValidationError as e:
    print(f"Validation error: {e}")
    print("Check your input data format")

except PermissionError as e:
    print(f"Permission denied: {e}")
    print(f"Required: {e.permission} on {e.resource}")
    print(f"User: {e.user_id}")

except NeonAPIError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")

    if e.status_code == 404:
        print("Resource not found")
    elif e.status_code == 429:
        print("Rate limited - slow down requests")
    elif e.status_code >= 500:
        print("Server error - try again later")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
import time
from neon_crm.exceptions import NeonAPIError

def create_with_retry(client, data, max_attempts=3):
    """Create account with retry logic."""
    for attempt in range(max_attempts):
        try:
            return client.accounts.create(data)
        except NeonAPIError as e:
            if e.status_code >= 500 and attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Server error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

result = create_with_retry(client, new_account)
```

## Best Practices

### 1. Use Configuration Files

```python
# Instead of hardcoding credentials
client = NeonClient(
    org_id="hardcoded",  # DON'T DO THIS
    api_key="hardcoded"
)

# Use environment variables or config files
client = NeonClient()  # BETTER
```

### 2. Enable Governance

```python
# Use appropriate roles for your use case
client = NeonClient(default_role="fundraiser")  # Not admin unless needed
```

### 3. Handle Errors Gracefully

```python
# Always wrap API calls in try/except
try:
    result = client.accounts.search(search_request)
except NeonAPIError as e:
    # Log error, notify user, or handle gracefully
    logger.error(f"Search failed: {e}")
```

### 4. Use Pagination Efficiently

```python
# For large datasets, process in chunks
for account in client.accounts.search(search_request):
    process_account(account)
    # Don't load everything into memory at once
```

### 5. Cache Field Discoveries

```python
# Field discovery is cached by default
# But you can disable if needed
client = NeonClient(enable_field_cache=False)
```

### 6. Validate Input Data

```python
def validate_email(email):
    import re
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

if validate_email(email):
    client.accounts.create(data)
else:
    raise ValueError(f"Invalid email: {email}")
```

### 7. Use Type Hints

```python
from typing import List, Dict, Any
from neon_crm import NeonClient

def get_recent_donors(
    client: NeonClient,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Get donors from the last N days."""
    # Implementation with type hints for better IDE support
    ...
```

### 8. Log Important Operations

```python
import logging

logger = logging.getLogger(__name__)

def create_donation(client, donation_data):
    logger.info(f"Creating donation for account {donation_data['accountId']}")
    try:
        result = client.donations.create(donation_data)
        logger.info(f"Created donation {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Failed to create donation: {e}")
        raise
```

### 9. Use Context Managers for Resources

```python
# If working with files or connections alongside SDK
from contextlib import contextmanager

@contextmanager
def neon_session(role="viewer"):
    client = NeonClient(default_role=role)
    try:
        yield client
    finally:
        # Cleanup if needed
        pass

with neon_session(role="fundraiser") as client:
    donations = client.donations.search(search_request)
```

### 10. Test with Governance Enabled

```python
# Test your code with governance enabled to catch permission issues early
import pytest
from neon_crm.governance.access_control import PermissionError

def test_viewer_cannot_create_accounts():
    client = NeonClient(default_role="viewer")

    with pytest.raises(PermissionError):
        client.accounts.create(test_account)
```

## Next Steps

- Review [Permissions Guide](../permissions.md) for access control
- Check [API Reference](../api/client.md) for detailed documentation
- See [Examples](../examples/basic.md) for more code samples
- Read [Advanced Topics](advanced-usage.md) for complex scenarios
