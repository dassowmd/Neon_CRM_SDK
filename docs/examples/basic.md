# Basic Examples

Common usage patterns and examples for the Neon CRM SDK.

## Table of Contents

- [Initialization](#initialization)
- [Searching](#searching)
- [Retrieving Records](#retrieving-records)
- [Creating Records](#creating-records)
- [Updating Records](#updating-records)
- [Deleting Records](#deleting-records)
- [Pagination](#pagination)
- [Error Handling](#error-handling)

## Initialization

### Simple Initialization

```python
from neon_crm import NeonClient

# Uses environment variables or config file
client = NeonClient()
```

### With Explicit Credentials

```python
from neon_crm import NeonClient

client = NeonClient(
    org_id="your-org-id",
    api_key="your-api-key",
    environment="production"
)
```

### With Governance

```python
from neon_crm import NeonClient

# Read-only access
client = NeonClient(default_role="viewer")

# Fundraiser access (donations, accounts, campaigns)
client = NeonClient(default_role="fundraiser")

# Full access
client = NeonClient(default_role="admin")
```

## Searching

### Search Accounts

```python
# Search for individual accounts
search_request = {
    "searchFields": [
        {"field": "Account Type", "operator": "EQUAL", "value": "Individual"}
    ],
    "outputFields": [
        "Account ID",
        "First Name",
        "Last Name",
        "Email 1",
        "City",
        "State/Province"
    ],
    "pagination": {
        "currentPage": 0,
        "pageSize": 50
    }
}

accounts = list(client.accounts.search(search_request))

for account in accounts:
    print(f"{account['First Name']} {account['Last Name']} - {account['Email 1']}")
```

### Search with Multiple Criteria

```python
# Search for accounts in California with email
search_request = {
    "searchFields": [
        {"field": "State/Province", "operator": "EQUAL", "value": "CA"},
        {"field": "Email 1", "operator": "NOT_BLANK"}
    ],
    "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"],
    "pagination": {"currentPage": 0, "pageSize": 100}
}

ca_accounts_with_email = list(client.accounts.search(search_request))
print(f"Found {len(ca_accounts_with_email)} accounts in CA with email")
```

### Search Donations by Date Range

```python
from datetime import datetime, timedelta

# Get donations from the last 30 days
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

search_request = {
    "searchFields": [
        {"field": "Donation Date", "operator": "GREATER_AND_EQUAL", "value": start_date},
        {"field": "Donation Date", "operator": "LESS_AND_EQUAL", "value": end_date}
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

# Calculate total
total = sum(float(d.get('Donation Amount', 0)) for d in recent_donations)
print(f"Total donations in last 30 days: ${total:,.2f}")
```

### Search Events

```python
# Search for upcoming events
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')

search_request = {
    "searchFields": [
        {"field": "Event Start Date", "operator": "GREATER_AND_EQUAL", "value": today}
    ],
    "outputFields": [
        "Event ID",
        "Event Name",
        "Event Start Date",
        "Event End Date",
        "Event Status"
    ],
    "pagination": {"currentPage": 0, "pageSize": 20}
}

upcoming_events = list(client.events.search(search_request))

for event in upcoming_events:
    print(f"{event['Event Name']} - {event['Event Start Date']}")
```

## Retrieving Records

### Get a Specific Account

```python
account_id = 12345
account = client.accounts.retrieve(account_id)

print(f"Name: {account['firstName']} {account['lastName']}")
print(f"Email: {account['primaryContact']['email1']}")
```

### Get a Specific Donation

```python
donation_id = 67890
donation = client.donations.retrieve(donation_id)

print(f"Amount: ${donation['amount']}")
print(f"Date: {donation['donationDate']}")
print(f"Account ID: {donation['accountId']}")
```

### Get Multiple Records

```python
account_ids = [123, 456, 789]

for account_id in account_ids:
    try:
        account = client.accounts.retrieve(account_id)
        print(f"Found: {account['firstName']} {account['lastName']}")
    except Exception as e:
        print(f"Account {account_id} not found: {e}")
```

## Creating Records

### Create an Individual Account

```python
new_account = {
    "individualAccount": {
        "accountCustomFields": [],
        "primaryContact": {
            "firstName": "Jane",
            "lastName": "Doe",
            "email1": "jane.doe@example.com",
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
                {
                    "type": "Mobile",
                    "number": "555-0123"
                }
            ]
        }
    }
}

result = client.accounts.create(new_account)
print(f"Created account ID: {result['id']}")
```

### Create a Company Account

```python
new_company = {
    "companyAccount": {
        "accountCustomFields": [],
        "name": "Acme Corporation",
        "primaryContact": {
            "firstName": "John",
            "lastName": "Smith",
            "email1": "john.smith@acme.com",
            "contactCustomFields": [],
            "addresses": [
                {
                    "addressType": "Work",
                    "addressLine1": "456 Business Blvd",
                    "city": "New York",
                    "stateProvince": {"code": "NY"},
                    "zipCode": "10001",
                    "country": {"name": "United States"}
                }
            ]
        }
    }
}

result = client.accounts.create(new_company)
print(f"Created company account ID: {result['id']}")
```

### Create a Donation

```python
from datetime import datetime

new_donation = {
    "accountId": 12345,
    "amount": 100.00,
    "donationDate": datetime.now().strftime('%Y-%m-%d'),
    "campaign": {"id": 5},
    "fund": {"id": 1},
    "payments": [
        {
            "paymentStatus": "Succeeded",
            "tenderType": {"id": 1},  # Credit Card
            "receivedDate": datetime.now().strftime('%Y-%m-%d'),
            "amount": 100.00
        }
    ]
}

result = client.donations.create(new_donation)
print(f"Created donation ID: {result['id']}")
```

## Updating Records

### Update an Account

```python
account_id = 12345

update_data = {
    "individualAccount": {
        "primaryContact": {
            "email1": "newemail@example.com",
            "phones": [
                {
                    "type": "Mobile",
                    "number": "555-9999"
                }
            ]
        }
    }
}

result = client.accounts.update(account_id, update_data)
print(f"Updated account {account_id}")
```

### Update Custom Fields

```python
account_id = 12345

update_data = {
    "individualAccount": {
        "accountCustomFields": [
            {
                "id": "123",  # Custom field ID
                "value": "New Value"
            },
            {
                "id": "456",
                "value": "2025-01-15"  # Date field
            }
        ]
    }
}

result = client.accounts.update(account_id, update_data)
print("Custom fields updated")
```

## Deleting Records

### Delete an Account

```python
account_id = 12345

try:
    client.accounts.delete(account_id)
    print(f"Deleted account {account_id}")
except Exception as e:
    print(f"Error deleting account: {e}")
```

### Soft Delete (Archive)

```python
# Some resources support archiving instead of hard delete
# Check the specific resource documentation
```

## Pagination

### Automatic Pagination

```python
# SDK automatically handles pagination
search_request = {
    "searchFields": [],
    "outputFields": ["Account ID", "First Name", "Last Name"],
    "pagination": {"currentPage": 0, "pageSize": 200}
}

# This fetches ALL accounts across all pages
all_accounts = list(client.accounts.search(search_request))
print(f"Total accounts: {len(all_accounts)}")
```

### Limit Results

```python
from itertools import islice

# Get only first 100 results
search_request = {
    "searchFields": [],
    "outputFields": ["Account ID", "First Name", "Last Name"],
    "pagination": {"currentPage": 0, "pageSize": 50}
}

first_100 = list(islice(client.accounts.search(search_request), 100))
print(f"Got {len(first_100)} accounts")
```

### Manual Pagination

```python
page_size = 50
current_page = 0
all_results = []

while True:
    search_request = {
        "searchFields": [],
        "outputFields": ["Account ID", "First Name"],
        "pagination": {"currentPage": current_page, "pageSize": page_size}
    }

    page_results = list(client.accounts.search(search_request))

    if not page_results:
        break

    all_results.extend(page_results)
    current_page += 1

    print(f"Fetched page {current_page}, total: {len(all_results)}")

print(f"Final total: {len(all_results)} accounts")
```

## Error Handling

### Basic Error Handling

```python
from neon_crm.exceptions import NeonAPIError, NeonValidationError

try:
    account = client.accounts.retrieve(12345)
except NeonAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
except NeonValidationError as e:
    print(f"Validation Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Handling Permission Errors

```python
from neon_crm.governance.access_control import PermissionError

try:
    # Attempt operation that may require permissions
    donations = list(client.donations.search(search_request))
except PermissionError as e:
    print(f"Permission denied: {e}")
    print(f"Required: {e.permission} on {e.resource}")
```

### Retry Logic for Network Errors

```python
import time
from neon_crm.exceptions import NeonAPIError

max_retries = 3
retry_delay = 5  # seconds

for attempt in range(max_retries):
    try:
        result = client.accounts.search(search_request)
        break
    except NeonAPIError as e:
        if e.status_code >= 500 and attempt < max_retries - 1:
            print(f"Server error, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        else:
            raise
```

### Validation Before API Calls

```python
def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

email = "jane.doe@example.com"

if validate_email(email):
    new_account = {
        "individualAccount": {
            "primaryContact": {
                "firstName": "Jane",
                "lastName": "Doe",
                "email1": email
            }
        }
    }
    result = client.accounts.create(new_account)
else:
    print("Invalid email format")
```

## Batch Operations

### Create Multiple Accounts

```python
accounts_to_create = [
    {
        "individualAccount": {
            "primaryContact": {
                "firstName": "Person",
                "lastName": f"Number{i}",
                "email1": f"person{i}@example.com"
            }
        }
    }
    for i in range(1, 11)
]

created_ids = []

for account_data in accounts_to_create:
    try:
        result = client.accounts.create(account_data)
        created_ids.append(result['id'])
        print(f"Created account {result['id']}")
    except Exception as e:
        print(f"Failed to create account: {e}")

print(f"Successfully created {len(created_ids)} accounts")
```

### Update Multiple Records

```python
account_updates = {
    12345: {"email1": "updated1@example.com"},
    12346: {"email1": "updated2@example.com"},
    12347: {"email1": "updated3@example.com"}
}

for account_id, updates in account_updates.items():
    try:
        update_data = {
            "individualAccount": {
                "primaryContact": updates
            }
        }
        client.accounts.update(account_id, update_data)
        print(f"Updated account {account_id}")
    except Exception as e:
        print(f"Failed to update {account_id}: {e}")
```

## Next Steps

- Read the [User Guide](../user-guide/basic-usage.md) for comprehensive documentation
- Review [Permissions Guide](../permissions.md) for access control
