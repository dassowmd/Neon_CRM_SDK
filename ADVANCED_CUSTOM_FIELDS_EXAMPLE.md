# Advanced Custom Field Management - Complete Guide

This guide demonstrates the enhanced custom field management capabilities built into the Neon CRM SDK, based on real-world migration patterns and comprehensive field type support.

## Table of Contents
1. [Basic Custom Field Operations](#basic-operations)
2. [Multi-Value Field Management](#multi-value-fields)
3. [Field Validation](#field-validation)
4. [Batch Operations](#batch-operations)
5. [Data Migration](#data-migration)
6. [Advanced Use Cases](#advanced-use-cases)

## Basic Operations

### Setting Custom Field Values

```python
from neon_crm import NeonClient

client = NeonClient(org_id="your_org", api_key="your_key")

# Set a simple text field
client.accounts.set_custom_field_value(123, "V-Notes", "Updated contact information")

# Set a multi-value field
client.accounts.set_custom_field_value(
    account_id=123,
    field_name="V-Volunteer Skills",
    value=["Technology", "Writing", "Data Entry"]
)

# Set multiple fields at once
result = client.accounts.set_multiple_custom_field_values(123, {
    "V-Notes": "Active volunteer",
    "V-Skills": ["Python", "JavaScript"],
    "V-Active": True,
    "V-Join Date": "2023-12-25"
})
print(f"Updated {result.successful} fields successfully")
```

### Getting Custom Field Values

```python
# Get a single field value (automatically parsed to correct Python type)
skills = client.accounts.get_custom_field_value(123, "V-Volunteer Skills")
print(skills)  # Output: ['Technology', 'Writing', 'Data Entry']

# Check field type information
field_info = client.accounts.find_custom_field_by_name("V-Volunteer Skills")
print(f"Field type: {field_info['displayType']}")  # Output: Checkbox
```

## Multi-Value Fields

### Adding Options Without Losing Existing Values

```python
# Add a new skill without losing existing ones
success = client.accounts.add_to_multivalue_field(
    resource_id=123,
    field_name="V-Volunteer Skills",
    new_option="Database Management"
)

if success:
    print("Successfully added new skill!")

    # Verify the addition
    updated_skills = client.accounts.get_custom_field_value(123, "V-Volunteer Skills")
    print(f"Updated skills: {updated_skills}")
    # Output: ['Technology', 'Writing', 'Data Entry', 'Database Management']
```

### Removing Options

```python
# Remove a specific option
client.accounts.remove_from_multivalue_field(
    resource_id=123,
    field_name="V-Volunteer Skills",
    option_to_remove="Data Entry"
)
```

### Working with Complex Multi-Value Scenarios

```python
# Handle the scenario from the notebook: add "Technology" to existing "Writing|Familiar with Word"
account_id = 6488
current_skills = client.accounts.get_custom_field_value(account_id, "V-Volunteer Skills")
print(f"Current: {current_skills}")  # ['Writing', 'Familiar with Word']

client.accounts.add_to_multivalue_field(account_id, "V-Volunteer Skills", "Technology")

updated_skills = client.accounts.get_custom_field_value(account_id, "V-Volunteer Skills")
print(f"Updated: {updated_skills}")  # ['Writing', 'Familiar with Word', 'Technology']
```

## Field Validation

### Validating Individual Fields

```python
from neon_crm.custom_field_validation import CustomFieldValidator

# Validate an email field
result = client.accounts.validate_custom_field_value("V-Email", "invalid-email")
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.message}")

# Validate a multi-value field against available options
result = client.accounts.validate_custom_field_value("V-Skills", ["Python", "InvalidSkill"])
if not result.is_valid:
    print("Validation failed:")
    for error in result.errors:
        print(f"  {error.message}")
```

### Comprehensive Field Type Validation

```python
# The validator handles all Neon CRM field types automatically
test_values = {
    "V-Email": "user@example.com",           # Email validation
    "V-Phone": "+1-555-123-4567",           # Phone format validation
    "V-Website": "https://example.com",      # URL validation
    "V-Join Date": "2023-12-25",            # Date format validation
    "V-Donation Amount": "150.75",          # Currency validation
    "V-Completion Rate": "85.5",            # Percentage validation
    "V-Active": True,                       # Boolean validation
    "V-Skills": ["Python", "JavaScript"],   # Multi-value validation
}

# Validate all fields
for field_name, value in test_values.items():
    result = client.accounts.validate_custom_field_value(field_name, value)
    print(f"{field_name}: {'✓' if result.is_valid else '✗'}")
```

## Batch Operations

### Bulk Adding Options to Multi-Value Fields

```python
from neon_crm.migration_tools import CustomFieldMigrationManager

# Create migration manager
migrator = CustomFieldMigrationManager(client, "accounts")

# Add "Technology" to all accounts that have volunteer skills but don't have Technology yet
result = migrator.bulk_add_option_to_multivalue(
    field_name="V-Volunteer Skills",
    new_option="Technology",
    resource_filter={"First Name": "Testy"},  # Filter to specific accounts
    dry_run=False  # Set to True to see what would be changed
)

print(f"Updated {result.successful_migrations} accounts")
print(f"Failed: {result.failed_migrations}")
if result.errors:
    print("Errors encountered:")
    for error in result.errors:
        print(f"  {error}")
```

### Batch Field Updates

```python
from neon_crm.custom_field_manager import CustomFieldUpdate

# Define multiple updates
updates = [
    CustomFieldUpdate(
        resource_id=123,
        field_name="V-Skills",
        value="Technology",
        operation="add"  # Add to multi-value field
    ),
    CustomFieldUpdate(
        resource_id=124,
        field_name="V-Notes",
        value="Updated profile",
        operation="replace"  # Replace text field
    ),
    CustomFieldUpdate(
        resource_id=125,
        field_name="V-Notes",
        value=" - Additional note",
        operation="append"  # Append to text field
    )
]

# Execute batch updates
manager = CustomFieldValueManager(client, "accounts")
result = manager.batch_update_custom_fields(updates)
print(f"Batch result: {result.successful} successful, {result.failed} failed")
```

## Data Migration

### Migrating from Old Field Structure (Based on Notebook)

```python
# Define the migration mapping (from the notebook experience)
migration_mapping = {
    'V-Tech Team': {
        'field': 'V-Volunteer Skills',
        'field_id': 163,
        'option': 'Technology'
    },
    'V-Data Entry': {
        'field': 'V-Volunteer Skills',
        'field_id': 163,
        'option': 'Data Entry'
    },
    'V-Social Media Team': {
        'field': 'V-Volunteer Skills',
        'field_id': 163,
        'option': 'Social Media'
    }
    # ... more mappings
}

# Create migration plan from notebook-style mapping
migrator = CustomFieldMigrationManager(client, "accounts")
migration_plan = migrator.create_migration_plan_from_notebook_mapping(migration_mapping)

# Analyze for conflicts before execution
conflict_report = migrator.analyze_migration_conflicts(migration_plan)
if conflict_report.field_conflicts:
    print("Field conflicts detected:")
    for conflict_type, fields in conflict_report.field_conflicts.items():
        print(f"  {conflict_type}: {fields}")

# Execute migration (dry run first)
migration_plan.dry_run = True
result = migrator.execute_migration_plan(migration_plan)
print(f"Dry run: Would migrate {result.total_resources} resources")
print(f"Projected success: {result.successful_migrations}")

# Execute for real
migration_plan.dry_run = False
real_result = migrator.execute_migration_plan(migration_plan)
print(f"Migration complete: {real_result.successful_migrations} successful")
```

### Custom Migration with Transformation

```python
from neon_crm.migration_tools import MigrationStrategy, MigrationMapping, MigrationPlan

# Define a custom transformation function
def parse_old_skills_text(old_text):
    """Convert old text format to list of skills."""
    if "tech" in old_text.lower():
        return ["Technology"]
    elif "writing" in old_text.lower():
        return ["Writing"]
    else:
        return [old_text.strip()]

# Create migration with transformation
mapping = MigrationMapping(
    source_field="V-Old Skills Text",
    target_field="V-Volunteer Skills",
    strategy=MigrationStrategy.REPLACE,
    transform_function=parse_old_skills_text
)

plan = MigrationPlan(
    mappings=[mapping],
    resource_filter={"V-Old Skills Text": "NOT_BLANK"},
    dry_run=True
)

result = migrator.execute_migration_plan(plan)
```

## Advanced Use Cases

### Intelligent Field Type Detection and Processing

```python
from neon_crm.custom_field_types import CustomFieldTypeMapper
from neon_crm.custom_field_processors import CustomFieldProcessorFactory

# Get field information
field_metadata = client.accounts.find_custom_field_by_name("V-Volunteer Skills")
field_info = CustomFieldTypeMapper.get_field_info(field_metadata)

print(f"Field: {field_info['name']}")
print(f"Display Type: {field_info['displayType']}")
print(f"Python Type: {field_info['pythonTypeName']}")
print(f"Is Multi-Value: {field_info['isMultiValue']}")
print(f"Requires Options: {field_info['requiresOptions']}")

# Use appropriate processor based on field type
processor = CustomFieldProcessorFactory.get_processor(field_metadata)
formatted_payload = processor.format_for_api(["Technology", "Writing"], field_metadata)
print(f"API Payload: {formatted_payload}")
```

### Search by Custom Field Values

```python
# Search for accounts with specific volunteer skills
tech_volunteers = client.accounts.search_by_custom_field_value(
    field_name="V-Volunteer Skills",
    value="Technology",
    operator="CONTAINS"
)

for volunteer in tech_volunteers:
    print(f"{volunteer['firstName']} {volunteer['lastName']} - Tech Volunteer")

# Complex search combining multiple criteria
search_request = {
    "searchFields": [
        {"field": "V-Volunteer Skills", "operator": "CONTAINS", "value": "Technology"},
        {"field": "V-Active", "operator": "EQUAL", "value": "true"},
        {"field": "First Name", "operator": "NOT_BLANK"}
    ],
    "outputFields": ["firstName", "lastName", "V-Volunteer Skills", "V-Notes"]
}

active_tech_volunteers = list(client.accounts.search(search_request))
print(f"Found {len(active_tech_volunteers)} active tech volunteers")
```

### Error Handling and Recovery

```python
try:
    # Attempt to set a field value with validation
    success = client.accounts.set_custom_field_value(
        resource_id=123,
        field_name="V-Email",
        value="potentially-invalid-email",
        validate=True
    )

    if not success:
        # Validation failed - get detailed validation results
        validation = client.accounts.validate_custom_field_value("V-Email", "potentially-invalid-email")
        if not validation.is_valid:
            print("Validation errors:")
            for error in validation.errors:
                print(f"  {error.message}")

        # Try to correct the issue
        corrected_value = input("Please enter a valid email: ")
        success = client.accounts.set_custom_field_value(123, "V-Email", corrected_value, validate=True)

except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error and continue processing
```

### Performance Optimization for Large Operations

```python
# For large migrations, use parallel processing and batching
migration_plan = MigrationPlan(
    mappings=migration_mappings,
    batch_size=50,        # Process 50 resources at a time
    max_workers=3,        # Use 3 threads for parallel processing
    dry_run=False
)

# Monitor progress
result = migrator.execute_migration_plan(migration_plan)

print(f"""
Migration Summary:
  Total Resources: {result.total_resources}
  Successful: {result.successful_migrations}
  Failed: {result.failed_migrations}
  Success Rate: {result.successful_migrations/result.total_resources*100:.1f}%
""")
```

## Key Benefits

1. **Type Safety**: Automatic field type detection and validation
2. **Data Integrity**: Preserve existing values when adding to multi-value fields
3. **Bulk Operations**: Efficient batch processing for large datasets
4. **Migration Support**: Tools for seamless data structure migrations
5. **Error Recovery**: Comprehensive validation and error handling
6. **Performance**: Parallel processing and optimized API usage
7. **Flexibility**: Support for all Neon CRM custom field types

## Best Practices

1. **Always validate before bulk operations**
2. **Use dry runs for migrations**
3. **Handle multi-value fields carefully to preserve existing data**
4. **Monitor migration progress and handle errors gracefully**
5. **Test transformations on sample data first**
6. **Use appropriate batch sizes for your data volume**
7. **Keep backups of critical data before major migrations**
