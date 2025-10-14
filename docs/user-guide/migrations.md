# Field Migrations

Comprehensive guide to using the migration tools for custom field data migrations in Neon CRM.

## Overview

The Neon CRM SDK provides powerful migration tools to help you migrate data between custom fields efficiently and safely. This is particularly useful for:

- **Data cleanup**: Consolidating similar fields
- **Field reorganization**: Moving data to better-structured fields
- **System migrations**: Bulk updates during CRM restructuring
- **Data validation**: Ensuring data integrity during field changes

## Quick Start

```python
from neon_crm import NeonClient, UserType

# Initialize client and create migration manager
client = NeonClient()
migration_manager = client.accounts.create_migration_manager(user_type=UserType.INDIVIDUAL)

# Define field mappings
field_mapping = {
    "Old Field Name": {"field": "New Field Name", "field_id": 123},
    "Another Old Field": {"field": "Target Field", "field_id": 124, "option": "Specific Option"}
}

# Create and execute migration plan
migration_plan = migration_manager.create_migration_plan_from_mapping(field_mapping)
results = migration_manager.execute_migration_plan(migration_plan)
```

## Resource-Specific Migration Managers

Each resource type has its own migration manager that handles resource-specific requirements:

### Accounts
```python
# Handles user_type parameter automatically
accounts_migrator = client.accounts.create_migration_manager(user_type=UserType.INDIVIDUAL)
```

### Events
```python
# Future: Would handle event-specific parameters
events_migrator = client.events.create_migration_manager()
```

### Donations
```python
# Simple resource with no special parameters
donations_migrator = client.donations.create_migration_manager()
```

## Migration Strategies

The migration system supports several strategies for handling data:

### REPLACE
```python
# Completely replace target field value with source field value
{"field": "Target Field", "strategy": "replace"}
```

### MERGE
```python
# Merge source value with existing target value
{"field": "Target Field", "strategy": "merge"}
```

### ADD_OPTION
```python
# Add specific option to multi-value field
{"field": "Multi Value Field", "field_id": 123, "option": "New Option Value"}
```

### COPY_IF_EMPTY
```python
# Only copy if target field is empty (default strategy)
{"field": "Target Field", "field_id": 123}
```

### TRANSFORM
```python
# Apply custom transformation function
{
    "field": "Target Field",
    "field_id": 123,
    "transform": lambda x: x.upper() if x else None
}
```

## Field Mapping Configuration

### Basic Field-to-Field Migration
```python
field_mapping = {
    "Source Field": {"field": "Target Field", "field_id": 123}
}
```

### Multi-Value Field Options
```python
field_mapping = {
    "Old Checkbox": {"field": "Skills", "field_id": 456, "option": "Programming"},
    "Another Checkbox": {"field": "Skills", "field_id": 456, "option": "Design"}
}
```

### Skipping Fields
```python
field_mapping = {
    "Old Field": "TODO",  # Will be skipped during migration
    "Active Field": {"field": "Target", "field_id": 123}
}
```

## Migration Plans

### Creating Migration Plans
```python
# From field mapping dictionary
migration_plan = migration_manager.create_migration_plan_from_mapping(field_mapping)

# For specific resource IDs only
targeted_plan = migration_manager.create_migration_plan_for_resources(
    field_mapping=field_mapping,
    resource_ids=[1001, 1002, 1003],
    dry_run=True
)
```

### Migration Plan Options
```python
# Configure migration settings
migration_plan.batch_size = 50        # Process 50 resources at a time
migration_plan.max_workers = 3        # Use 3 parallel threads
migration_plan.dry_run = True         # Safe testing mode
migration_plan.resource_filter = {    # Filter which resources to migrate
    "Status": "Active"
}
```

## Executing Migrations

### Dry Run Testing
```python
# Always test first with dry_run=True
migration_plan.dry_run = True
results = migration_manager.execute_migration_plan(migration_plan)

print(f"Would migrate {results.total_resources} resources")
print(f"Successful: {results.successful_migrations}")
print(f"Failed: {results.failed_migrations}")
```

### Production Migration
```python
# Only after successful dry run testing
migration_plan.dry_run = False
results = migration_manager.execute_migration_plan(migration_plan)
```

### Targeted Migration
```python
# Migrate only specific resources
specific_accounts = [6488, 6489, 6490]
targeted_plan = migration_manager.create_migration_plan_for_resources(
    field_mapping=field_mapping,
    resource_ids=specific_accounts,
    dry_run=False
)
results = migration_manager.execute_migration_plan(targeted_plan)
```

## Conflict Analysis

Before running migrations, analyze potential conflicts:

```python
conflict_report = migration_manager.analyze_migration_conflicts(migration_plan)

print(f"Missing source fields: {len(conflict_report.field_conflicts.get('missing_source', []))}")
print(f"Missing target fields: {len(conflict_report.field_conflicts.get('missing_target', []))}")
print(f"Type conflicts: {len(conflict_report.type_conflicts)}")

# Review suggestions
for suggestion in conflict_report.resolution_suggestions:
    print(f"💡 {suggestion}")
```

## Performance Optimization

### Field-Specific Fetching
The migration system automatically optimizes performance by:
- Only fetching required fields (source + target + ID)
- Avoiding expensive "fetch all fields" operations
- Using targeted searches instead of full scans

### Batch Processing
```python
# Configure batch sizes for optimal performance
migration_plan.batch_size = 100      # Smaller batches for complex migrations
migration_plan.max_workers = 5       # More workers for I/O bound operations
```

### Targeted Migrations
```python
# Process subsets of data for better control
batch_1_ids = [1, 2, 3, 4, 5]
batch_2_ids = [6, 7, 8, 9, 10]

for batch_ids in [batch_1_ids, batch_2_ids]:
    batch_plan = migration_manager.create_migration_plan_for_resources(
        field_mapping=field_mapping,
        resource_ids=batch_ids,
        dry_run=False
    )
    results = migration_manager.execute_migration_plan(batch_plan)
    print(f"Batch complete: {results.successful_migrations} successful")
```

## Error Handling

### Understanding Migration Results
```python
results = migration_manager.execute_migration_plan(migration_plan)

# Check for errors
if results.errors:
    print("Migration errors occurred:")
    for error in results.errors:
        print(f"❌ {error}")

# Check for warnings
if results.warnings:
    print("Migration warnings:")
    for warning in results.warnings:
        print(f"⚠️ {warning}")

# Detailed results
print(f"📊 Migration Summary:")
print(f"  Total resources: {results.total_resources}")
print(f"  Successful: {results.successful_migrations}")
print(f"  Failed: {results.failed_migrations}")
print(f"  Skipped: {results.skipped_migrations}")
```

### Common Error Scenarios
- **Missing Fields**: Source or target field doesn't exist
- **Type Conflicts**: Incompatible field types
- **Validation Failures**: Data doesn't meet target field requirements
- **Permission Issues**: Insufficient access to modify fields
- **Rate Limits**: API throttling during large migrations

## Best Practices

### 1. Always Test First
```python
# ALWAYS run dry runs before production migrations
migration_plan.dry_run = True
test_results = migration_manager.execute_migration_plan(migration_plan)
# Review results carefully before proceeding
```

### 2. Use Targeted Testing
```python
# Test on a small subset first
test_plan = migration_manager.create_migration_plan_for_resources(
    field_mapping=field_mapping,
    resource_ids=[6488],  # Single test account
    dry_run=True
)
```

### 3. Analyze Conflicts
```python
# Always check for conflicts before migration
conflict_report = migration_manager.analyze_migration_conflicts(migration_plan)
if conflict_report.field_conflicts or conflict_report.type_conflicts:
    print("⚠️ Resolve conflicts before proceeding")
```

### 4. Monitor Progress
```python
# For large migrations, process in batches
all_resource_ids = [1, 2, 3, ..., 10000]
batch_size = 100

for i in range(0, len(all_resource_ids), batch_size):
    batch_ids = all_resource_ids[i:i+batch_size]
    batch_plan = migration_manager.create_migration_plan_for_resources(
        field_mapping=field_mapping,
        resource_ids=batch_ids,
        dry_run=False
    )
    results = migration_manager.execute_migration_plan(batch_plan)
    print(f"Batch {i//batch_size + 1}: {results.successful_migrations} successful")
```

### 5. Backup Strategy
- Always have a data backup before major migrations
- Consider exporting affected records before migration
- Plan rollback procedures for critical data

## Troubleshooting

### Common Issues

**Migration shows 0 resources processed**
- Check if source fields have any data
- Verify field names are correct
- Ensure resource filter isn't too restrictive

**High failure rates**
- Review field compatibility (types, validation rules)
- Check for data format issues
- Verify target field configurations

**Performance issues**
- Reduce batch sizes
- Limit concurrent workers
- Use targeted migrations instead of full scans

### Debug Mode
```python
import logging
logging.getLogger('neon_crm.migration_tools').setLevel(logging.DEBUG)

# Now migration operations will show detailed logs
results = migration_manager.execute_migration_plan(migration_plan)
```

## Advanced Features

### Custom Transform Functions
```python
def normalize_phone(phone_value):
    """Custom function to normalize phone numbers."""
    if not phone_value:
        return None
    # Remove all non-digits
    cleaned = ''.join(c for c in str(phone_value) if c.isdigit())
    if len(cleaned) == 10:
        return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
    return phone_value

# Use in field mapping
field_mapping = {
    "Old Phone": {
        "field": "Formatted Phone",
        "field_id": 789,
        "transform": normalize_phone
    }
}
```

### Conditional Migrations
```python
def conditional_copy(source_value):
    """Only copy if value meets certain criteria."""
    if source_value and len(str(source_value)) > 5:
        return source_value
    return None  # Don't migrate short values
```

## API Reference

For detailed API documentation, see:
- [`BaseMigrationManager`](../api/migration-tools/base.md)
- [`AccountsMigrationManager`](../api/migration-tools/accounts.md)
- [`MigrationPlan`](../api/migration-tools/plans.md)
- [`MigrationResult`](../api/migration-tools/results.md)
