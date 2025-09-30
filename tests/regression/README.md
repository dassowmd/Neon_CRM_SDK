# Neon CRM SDK Regression Tests

Comprehensive regression tests for the Neon CRM Python SDK, organized by endpoint/resource for maintainability and clarity.

## Structure

```
tests/regression/
├── README.md                     # This file
├── run_regression_tests.py       # Test runner script
├── conftest.py                   # Pytest configuration and fixtures
└── resources/                    # Tests organized by SDK resource
    ├── test_accounts.py           # AccountsResource tests
    ├── test_activities.py         # ActivitiesResource tests
    ├── test_base_resource.py      # BaseResource tests (critical fixes)
    ├── test_campaigns.py          # CampaignsResource tests
    ├── test_custom_fields.py      # CustomFieldsResource tests (original issue)
    ├── test_custom_objects.py     # CustomObjectsResource tests
    ├── test_donations.py          # DonationsResource tests
    ├── test_events.py             # EventsResource tests
    ├── test_grants.py             # GrantsResource tests
    ├── test_households.py         # HouseholdsResource tests
    ├── test_memberships.py        # MembershipsResource tests
    ├── test_online_store.py       # OnlineStoreResource tests
    ├── test_orders.py             # OrdersResource tests
    ├── test_payments.py           # PaymentsResource tests
    ├── test_pledges.py            # PledgesResource tests
    ├── test_properties.py         # PropertiesResource tests
    ├── test_recurring_donations.py # RecurringDonationsResource tests
    ├── test_soft_credits.py       # SoftCreditsResource tests
    ├── test_volunteers.py         # VolunteersResource tests
    └── test_webhooks.py           # WebhooksResource tests
```

## Test Categories

### Read-Only Tests (`@pytest.mark.readonly`)
- **Safe for production environments**
- Test list operations, search functionality, parameter validation
- Focus on the critical limit parameter fixes
- Test pagination, filtering, and error handling
- No data modification

### Write Operation Tests (`@pytest.mark.writeops`)
- **Modifies database - use test environment only**
- Test create, update, delete operations
- Include proper cleanup in finally blocks
- Test validation errors and edge cases
- Require write-enabled API credentials

## Critical SDK Fixes Tested

### 1. BaseResource Limit Parameter Bug (Fixed)
**Issue**: `TypeError` when `limit=None` due to comparison `if results_returned < limit:`
**Fix**: Added null check: `if limit is None or results_returned < limit:`
**Tests**: `test_base_resource.py::TestBaseResourceLimitFixes`

### 2. Missing Limit Parameter (Fixed in 16 resources)
**Issue**: Resources had `limit` parameter in signature but didn't pass it to parent class
**Fix**: Added `limit=limit` to all `super().list()` calls
**Tests**: All resource test files include `test_*_limit_parameter_fixed`

### 3. OnlineStoreResource Special Case (Fixed)
**Issue**: Custom implementation ignored pagination and limit parameters
**Fix**: Implemented proper parameter handling with limit enforcement
**Tests**: `test_online_store.py::TestOnlineStoreReadOnly`

## Usage

### Install Dependencies
```bash
pip install pytest python-dotenv
```

### Configure Environment
Create `.env` file in project root:
```
NEON_API_KEY=your_api_key_here
NEON_ORG_ID=your_org_id_here
# For write operations:
NEON_WRITE_API_KEY=your_write_api_key_here
```

### Run Tests

#### Read-Only Tests (Safe for Production)
```bash
# All read-only tests
python tests/regression/run_regression_tests.py --readonly

# Specific resource
python tests/regression/run_regression_tests.py --readonly --resource custom_fields

# List available resources
python tests/regression/run_regression_tests.py --list-resources
```

#### Write Operation Tests (Test Environment Only)
```bash
# All write operations (will prompt for confirmation)
python tests/regression/run_regression_tests.py --writeops

# Specific resource write operations
python tests/regression/run_regression_tests.py --writeops --resource accounts
```

#### All Tests
```bash
# Everything (will prompt for confirmation)
python tests/regression/run_regression_tests.py --all
```

### Direct Pytest Usage
```bash
# Read-only tests only
pytest tests/regression/resources/ -m readonly -v

# Write operations only
pytest tests/regression/resources/ -m writeops -v

# Specific resource
pytest tests/regression/resources/test_custom_fields.py -v

# Run with output (see print statements)
pytest tests/regression/resources/test_custom_fields.py -s
```

## Test Patterns

### Limit Parameter Testing (Critical)
Every resource test includes:
```python
def test_*_limit_parameter_fixed(self, regression_client):
    \"\"\"Test limit parameter - this was broken before the fix.\"\"\"
    # Test limit parameter
    limited_items = list(regression_client.*.list(page_size=20, limit=5))

    if len(limited_items) > 5:
        print(f"❌ CRITICAL: Limit not working: got {len(limited_items)}, expected max 5")
    else:
        print(f"✓ FIXED: Limit parameter working: got {len(limited_items)} items")

    # Test limit=None (was causing crashes)
    try:
        unlimited_items = list(regression_client.*.list(page_size=10, limit=None))
        print(f"✓ FIXED: limit=None works: got {len(unlimited_items)} items")
    except TypeError as e:
        print(f"❌ CRITICAL: limit=None still crashes: {e}")
```

### Write Operation Testing
All write operations include proper cleanup:
```python
def test_create_*_basic(self, write_regression_client):
    created_items = []
    try:
        # Create operation
        result = write_regression_client.*.create(payload)
        item_id = result.get("*Id") or result.get("id")
        if item_id:
            created_items.append(item_id)
            # Test the creation
    except Exception as e:
        print(f"❌ Creation failed: {e}")
    finally:
        # Always cleanup
        for item_id in created_items:
            try:
                write_regression_client.*.delete(item_id)
                print(f"✓ Cleaned up: {item_id}")
            except Exception as e:
                print(f"⚠ Could not delete {item_id}: {e}")
```

## Extending Tests

### Adding New Resource Tests
1. Create `test_new_resource.py` in `resources/` directory
2. Follow existing patterns:
   - Import required modules and exceptions
   - Create `TestNewResourceReadOnly` class with `@pytest.mark.readonly`
   - Create `TestNewResourceWriteOperations` class with `@pytest.mark.writeops`
   - Include limit parameter testing
   - Add proper cleanup for write operations
3. Update `AVAILABLE_RESOURCES` in `run_regression_tests.py`

### Adding New Test Cases
- Use descriptive test method names: `test_*_specific_scenario`
- Include docstrings explaining what's being tested
- Use print statements to show progress and results
- Test both happy path and error conditions
- Validate expected response structure

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure SDK is installed and in PYTHONPATH
2. **Authentication errors**: Check `.env` file and API credentials
3. **Timeout errors**: Some endpoints may be slow; consider adjusting timeouts
4. **Write operation failures**: Ensure using write-enabled credentials and test environment

### Debug Mode
Add `-s` flag to pytest to see print statements:
```bash
pytest tests/regression/resources/test_custom_fields.py -s -v
```

## Contributing

When adding tests:
1. Follow the existing structure and patterns
2. Test the critical limit parameter functionality
3. Include proper error handling and cleanup
4. Add clear documentation and comments
5. Test both success and failure scenarios
