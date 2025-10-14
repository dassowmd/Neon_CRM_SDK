# Migration Plan Export/Import Documentation

The Neon CRM SDK now supports exporting migration plans to human-readable formats, allowing for manual review and validation before execution. This feature addresses the need for safer, reviewable migrations.

## Overview

The export/import functionality allows you to:

1. **Export** migration plans to YAML, JSON, or CSV formats
2. **Review** plans manually before execution
3. **Edit** plans in text editors or spreadsheet applications
4. **Import** and validate plans before execution
5. **Share** plans with team members for review

## Key Benefits

- **Human Review**: Plans can be reviewed by humans before execution
- **Version Control**: Text-based plans can be stored in git repositories
- **Collaboration**: Plans can be shared and reviewed by teams
- **Audit Trail**: Exported plans serve as documentation of migration strategies
- **Safety**: Import validation catches issues before execution

## Usage

### Command Line Tool

The `migration_plan_manager.py` tool provides easy command-line access:

```bash
# Export a migration plan
python tools/migration_plan_manager.py export --output migration_plan.yaml --format yaml

# Import and validate a plan
python tools/migration_plan_manager.py import --input migration_plan.yaml --validate

# Create a template for manual editing
python tools/migration_plan_manager.py template --output template.yaml

# Show information about a plan
python tools/migration_plan_manager.py info --input migration_plan.yaml
```

### Programmatic API

```python
from neon_crm import NeonClient
from neon_crm.migration_tools.accounts import AccountsMigrationManager

# Initialize client and migration manager
client = NeonClient()
migration_manager = AccountsMigrationManager(client.accounts, client, "accounts")

# Create a migration plan
migration_plan = migration_manager.create_migration_plan_from_mapping(field_mapping)

# Export for review
exported_file = migration_manager.export_migration_plan(
    migration_plan,
    "migration_plan.yaml",
    format="yaml"
)

# Later, import and execute
reviewed_plan = migration_manager.import_migration_plan("migration_plan.yaml")
result = migration_manager.execute_migration_plan(reviewed_plan)
```

## Export Formats

### YAML Format (Recommended)

YAML provides the best balance of human readability and completeness:

```yaml
# Neon CRM Migration Plan Export
# Generated: 2025-10-09T23:07:37.633863
#
# IMPORTANT: Review this plan carefully before importing and executing!

metadata:
  export_timestamp: '2025-10-09T23:07:37.633863'
  plan_summary:
    total_mappings: 3
    resource_ids_count: 3
    dry_run: true
    smart_migration: true

plan:
  mappings:
  - source_field: V-Canvassing
    target_field: V-Volunteer Campaign & Election Activities
    strategy: add_option
    preserve_source: false
    validation_required: true
    transform_function:
      has_function: true
      note: Transform function cannot be serialized - will need to be recreated on import

  resource_ids: [6488, 1234, 5678]
  cleanup_only: false
  smart_migration: true
  batch_size: 50
  max_workers: 3
  dry_run: true
```

### JSON Format

Useful for programmatic processing:

```json
{
  "metadata": {
    "export_timestamp": "2025-10-09T23:07:37.633863",
    "plan_summary": {
      "total_mappings": 3,
      "resource_ids_count": 3,
      "dry_run": true
    }
  },
  "plan": {
    "mappings": [
      {
        "source_field": "V-Canvassing",
        "target_field": "V-Volunteer Campaign & Election Activities",
        "strategy": "add_option",
        "preserve_source": false
      }
    ]
  }
}
```

### CSV Format

Best for spreadsheet applications and simple review:

```csv
source_field,target_field,strategy,preserve_source,validation_required,has_transform_function,notes
V-Canvassing,V-Volunteer Campaign & Election Activities,add_option,False,True,True,Requires transform function recreation
V-Data Entry,V-Volunteer Skills,add_option,False,True,True,Requires transform function recreation
```

## Workflow Examples

### 1. Safe Migration Review Workflow

```bash
# 1. Create and export migration plan
python create_migration_plan.py  # Your custom script
python tools/migration_plan_manager.py export --output review_plan.yaml

# 2. Review the plan manually
# - Check field mappings are correct
# - Verify target fields exist
# - Review strategies and options
# - Add any manual edits needed

# 3. Import and validate
python tools/migration_plan_manager.py import --input review_plan.yaml --validate

# 4. Execute (in your code)
python execute_migration.py review_plan.yaml
```

### 2. Team Collaboration Workflow

```bash
# Developer creates initial plan
python tools/migration_plan_manager.py template --output v_fields_migration.yaml

# Edit template to specify target fields and strategies
# Commit to git repository

# Team review via pull request
# - Review field mappings
# - Validate strategies
# - Check for conflicts

# Execute approved plan
python execute_approved_migration.py v_fields_migration.yaml
```

### 3. Incremental Migration Workflow

```bash
# Export plan for Phase 1 fields
python tools/migration_plan_manager.py export --output phase1_plan.yaml

# Execute Phase 1
python execute_migration.py phase1_plan.yaml

# Export plan for Phase 2 fields
python tools/migration_plan_manager.py export --output phase2_plan.yaml

# Execute Phase 2
python execute_migration.py phase2_plan.yaml
```

## Validation Features

When importing plans, the system validates:

- **Field Existence**: Source and target fields exist in the CRM
- **Type Compatibility**: Field types are compatible for the migration strategy
- **Plan Freshness**: Warning if plan is stale (>24 hours old)
- **Structure Integrity**: Plan structure is valid and complete

## Limitations

### Transform Functions

Transform functions cannot be serialized and must be recreated when importing:

```python
# After importing, you may need to recreate transform functions
for mapping in imported_plan.mappings:
    if mapping.source_field == "V-Canvassing":
        mapping.transform_function = lambda x: "Canvassing/literature Drop" if x else None
```

### Large Resource Lists

For plans with many specific resource IDs, consider using resource filters instead:

```yaml
# Instead of listing thousands of IDs
resource_ids: [1, 2, 3, ..., 10000]

# Use a filter
resource_filter:
  date_range: "2024-01-01,2024-12-31"
  field_criteria: "V-Canvassing"
```

## Security Considerations

- **Review All Plans**: Never execute imported plans without manual review
- **Validate Sources**: Only import plans from trusted sources
- **Test First**: Always run with `dry_run=True` initially
- **Backup Data**: Ensure database backups before executing large migrations

## Integration with Existing Code

The export/import functionality integrates seamlessly with existing migration tools:

```python
# Existing migration code
migration_plan = migration_manager.create_migration_plan_from_mapping(mapping)

# Add export step
export_path = migration_manager.export_migration_plan(
    migration_plan,
    f"migration_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
)
print(f"Plan exported for review: {export_path}")

# Manual review happens here...

# Import reviewed plan
reviewed_plan = migration_manager.import_migration_plan(export_path)

# Execute reviewed plan
result = migration_manager.execute_migration_plan(reviewed_plan)
```

## Best Practices

1. **Always Export Before Execution**: Export plans for audit trails
2. **Use Descriptive Filenames**: Include dates and migration scope
3. **Store in Version Control**: Keep plans in git for history
4. **Review with Team**: Have migrations reviewed before execution
5. **Test with Small Datasets**: Validate plans with limited resource IDs first
6. **Document Changes**: Include notes in exported plans explaining modifications

## Troubleshooting

### Import Errors

```bash
# If import fails, check the plan structure
python tools/migration_plan_manager.py info --input problematic_plan.yaml

# Validate field names exist
python tools/migration_plan_manager.py import --input plan.yaml --validate
```

### Missing Transform Functions

```python
# Recreate transform functions after import
def recreate_transform_functions(migration_plan):
    for mapping in migration_plan.mappings:
        if mapping.source_field == "V-Canvassing":
            mapping.transform_function = lambda x: "Canvassing/literature Drop" if x else None
        elif mapping.source_field == "V-Data Entry":
            mapping.transform_function = lambda x: "Data Entry" if x else None
```

### Performance Considerations

For large migrations, consider:
- Smaller batch sizes for better error handling
- Resource ID lists instead of broad filters
- Incremental migrations using multiple smaller plans

## Future Enhancements

- **Visual Plan Editor**: Web UI for editing migration plans
- **Plan Comparison**: Diff functionality between plan versions
- **Automated Validation**: Integration with CI/CD pipelines
- **Progress Tracking**: Real-time execution progress for imported plans
