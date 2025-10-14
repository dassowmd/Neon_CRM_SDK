# Field Name Updates and Standardization

This document tracks the field name standardization efforts across the Neon CRM SDK codebase.

## Summary of Changes

### Updated Files
1. **docs/field_name_standards.md** - New comprehensive standards document
2. **tools/migration_plan_manager.py** - Updated example field names
3. **tools/mapping_validator_test.py** - Standardized test examples
4. **docs/fast_migration_discovery.md** - Updated documentation examples
5. **src/neon_crm/migration_tools/fast_discovery.py** - Improved field suggestion logic
6. **CUSTOM_FIELD_ENHANCEMENT_SUMMARY.md** - Updated API examples

### Key Improvements

#### 1. Separated Combined Fields
**Before**: `V-Phone/Text Banking`
**After**:
- `V-Phone Banking`
- `V-Text Banking`

**Rationale**: Separate fields are clearer and easier to migrate individually.

#### 2. Standardized Field Names
**Before**: Various inconsistent examples
**After**: Consistent with field_name_standards.md

#### 3. Improved Categorization
**Before**: Generic or unclear target suggestions
**After**: Four primary volunteer categories:
- `V-Volunteer Skills` - Technical and administrative abilities
- `V-Volunteer Campaign & Election Activities` - Political campaign work
- `V-Volunteer Interests` - General areas of interest
- `V-Volunteer Availability` - Time and scheduling preferences

#### 4. Enhanced Migration Logic
Updated the fast discovery module to better categorize fields based on keywords:
- **Skills**: data, entry, admin, office, technology, tech → `V-Volunteer Skills`
- **Campaign**: campaign, election, vote, canvass, phone, text, banking → `V-Volunteer Campaign & Election Activities`
- **Interests**: interest, want, like, event, planning, food, hospitality → `V-Volunteer Interests`
- **Availability**: availability, time, schedule → `V-Volunteer Availability`

## Migration Examples

### Field Consolidation Patterns
```python
# Common migration mappings using standardized names
migration_mappings = {
    # Campaign activities
    "V-Canvassing": "V-Volunteer Campaign & Election Activities",
    "V-Phone Banking": "V-Volunteer Campaign & Election Activities",
    "V-Text Banking": "V-Volunteer Campaign & Election Activities",

    # Skills and technical work
    "V-Data Entry": "V-Volunteer Skills",
    "V-Technology Support": "V-Volunteer Skills",
    "V-Office Support": "V-Volunteer Skills",

    # General interests
    "V-Event Planning": "V-Volunteer Interests",
    "V-Food & Hospitality": "V-Volunteer Interests",
    "V-Transportation": "V-Volunteer Interests"
}
```

### Testing Examples
```python
# Use these field names in tests and examples
valid_test_fields = [
    "firstName",                    # Standard field
    "lastName",                     # Standard field
    "email1",                       # Standard field
    "V-Volunteer Skills",           # Custom multi-select
    "V-Volunteer Interests",        # Custom multi-select
    "V-Volunteer Campaign & Election Activities"  # Custom multi-select
]

invalid_test_fields = [
    "NonExistentField",             # For negative tests
    "InvalidField123",              # For error handling tests
    "Missing-Field"                 # For validation tests
]
```

## Documentation Standards

### Field Name Examples to Use
✅ **Good Examples**:
- `V-Volunteer Skills` - Clear and descriptive
- `V-Volunteer Campaign & Election Activities` - Specific but broad enough
- `firstName` - Standard Neon field
- `accountId` - Standard identifier

❌ **Avoid These Examples**:
- `V-Skills` - Too generic
- `V-Tech Team` - Too specific, not scalable
- `Custom Field 1` - Not descriptive
- `Field123` - Not meaningful

### Code Comment Standards
When using field names in code examples, include comments explaining the field type:

```python
# Standard field examples
"firstName"    # Standard text field
"accountId"    # Standard numeric field

# Custom field examples
"V-Volunteer Skills"    # Custom MultiSelect field
"V-Volunteer Interests" # Custom MultiSelect field
```

## Quality Assurance

### Verification Checklist
- [ ] All examples use standardized field names
- [ ] Documentation is consistent across files
- [ ] Test examples are realistic and useful
- [ ] Migration examples follow best practices
- [ ] Field suggestions logic is accurate

### Automated Checks
Consider adding these checks to CI/CD:
1. Grep for outdated field name patterns
2. Validate example field names against standards
3. Check for consistency across documentation

## Future Maintenance

### When to Update Field Names
- New common field patterns emerge
- User feedback on confusing examples
- Neon CRM introduces new standard fields
- Migration patterns evolve

### Update Process
1. Update docs/field_name_standards.md first
2. Search codebase for old patterns: `grep -r "old-pattern" .`
3. Update all found instances
4. Test updated examples
5. Document changes in this file

## Related Files

### Primary Standards
- `docs/field_name_standards.md` - Main standards document

### Updated Documentation
- `docs/fast_migration_discovery.md`
- `CUSTOM_FIELD_ENHANCEMENT_SUMMARY.md`

### Updated Code
- `src/neon_crm/migration_tools/fast_discovery.py`

### Updated Tools
- `tools/migration_plan_manager.py`
- `tools/mapping_validator_test.py`

Last Updated: 2025-01-09
