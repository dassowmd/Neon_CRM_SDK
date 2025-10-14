# Field Name Standards and Examples

This document provides standardized field name examples for use throughout the Neon CRM SDK documentation and code examples.

## Standard Field Names

### Account Fields
- `accountId` - Unique account identifier
- `firstName` - Individual's first name
- `lastName` - Individual's last name
- `preferredName` - Individual's preferred name
- `companyName` - Organization/company name
- `email1`, `email2`, `email3` - Primary, secondary, and tertiary email addresses
- `phone1`, `phone2`, `phone3` - Primary, secondary, and tertiary phone numbers
- `accountType` - Type of account (INDIVIDUAL, ORGANIZATION)
- `city` - City in address
- `stateProvince` - State or province
- `zipCode` - Postal/ZIP code
- `country` - Country
- `dateCreated` - Account creation date
- `dateModified` - Last modification date
- `source` - Source of account creation

### Donation Fields
- `id` - Donation ID
- `accountId` - Associated account ID
- `amount` - Donation amount
- `date` - Donation date
- `campaign` - Associated campaign
- `fund` - Associated fund
- `purpose` - Donation purpose
- `paymentMethod` - Payment method used

### Event Fields
- `id` - Event ID
- `name` - Event name
- `startDate` - Event start date
- `endDate` - Event end date
- `category` - Event category
- `status` - Event status
- `maximumAttendees` - Maximum number of attendees

## Volunteer Custom Field Examples

These examples represent common volunteer management custom fields that organizations use in Neon CRM.

### Current Standard V-Fields
Based on real-world Neon CRM implementations, these are the recommended V-field names:

#### Primary Volunteer Interest Categories
- `V-Volunteer Campaign & Election Activities` - Political campaign work
- `V-Volunteer Skills` - General volunteer skills
- `V-Volunteer Interests` - Areas of volunteer interest
- `V-Volunteer Availability` - Availability for volunteer work

#### Specific Volunteer Activities
- `V-Canvassing` - Door-to-door outreach activities
- `V-Data Entry` - Administrative data management
- `V-Phone Banking` - Phone-based outreach
- `V-Text Banking` - Text message outreach
- `V-Digital Organizing` - Online campaign activities
- `V-Event Planning` - Event organization and management
- `V-Graphic Design` - Creative design work
- `V-Writing & Communications` - Content creation
- `V-Translation Services` - Language translation
- `V-Office Support` - General administrative tasks
- `V-Food & Hospitality` - Event catering and hospitality
- `V-Transportation` - Driving and logistics support
- `V-Technology Support` - IT and technical assistance

#### Specialized Skills
- `V-Legal Support` - Legal expertise
- `V-Financial Management` - Accounting and finance
- `V-Social Media` - Social media management
- `V-Photography` - Photo documentation
- `V-Video Production` - Video creation and editing
- `V-Training & Education` - Teaching and training others

### Multi-Value Field Structure

For multi-select volunteer fields, use this structure:
- **Field Type**: MultiSelect
- **Options**: Individual activities within the category
- **Usage**: Allows volunteers to select multiple specific activities

Example:
```
Field Name: V-Volunteer Skills
Options:
- Technology
- Communication
- Organization
- Leadership
- Creative
- Administrative
```

### Migration Mapping Examples

Common migration patterns for consolidating V-fields:

#### Consolidation Mappings
```python
# Consolidate specific activities into broader categories
{
    "V-Canvassing": "V-Volunteer Campaign & Election Activities",
    "V-Phone Banking": "V-Volunteer Campaign & Election Activities",
    "V-Text Banking": "V-Volunteer Campaign & Election Activities",
    "V-Data Entry": "V-Volunteer Skills",
    "V-Graphic Design": "V-Volunteer Skills",
    "V-Event Planning": "V-Volunteer Interests",
    "V-Food Team": "V-Volunteer Interests",
    "V-Driver assistance": "V-Volunteer Availability"
}
```

#### Skill-Based Groupings
```python
# Group by skill type
{
    "V-Data Entry": "V-Administrative Skills",
    "V-Office Support": "V-Administrative Skills",
    "V-Graphic Design": "V-Creative Skills",
    "V-Photography": "V-Creative Skills",
    "V-Phone Banking": "V-Communication Skills",
    "V-Writing & Communications": "V-Communication Skills"
}
```

## Documentation Examples

### DO Use These Examples
- `V-Volunteer Skills` (clear, standardized)
- `V-Volunteer Campaign & Election Activities` (descriptive)
- `firstName` (standard field)
- `accountId` (standard field)

### DON'T Use These Examples
- `V-Skills` (too generic)
- `V-Tech Team` (outdated, too specific)
- `Custom Field 1` (meaningless)
- `Field123` (not descriptive)

## Code Example Standards

### Search Operations
```python
# Good: Use descriptive field names
search_request = {
    "searchFields": [
        {"field": "firstName", "operator": "EQUAL", "value": "John"},
        {"field": "V-Volunteer Skills", "operator": "NOT_BLANK"}
    ],
    "outputFields": ["accountId", "firstName", "lastName", "V-Volunteer Skills"]
}
```

### Migration Examples
```python
# Good: Clear source and target mapping
migration_mapping = {
    "V-Data Entry": "V-Volunteer Skills",
    "V-Phone Banking": "V-Volunteer Campaign & Election Activities",
    "V-Event Planning": "V-Volunteer Interests"
}
```

### Custom Field Operations
```python
# Good: Descriptive field names in operations
client.accounts.set_custom_field_value(
    account_id=12345,
    field_name="V-Volunteer Skills",
    value=["Technology", "Communication"]
)

client.accounts.add_to_multivalue_field(
    account_id=12345,
    field_name="V-Volunteer Interests",
    new_option="Event Planning"
)
```

## Field Naming Conventions

### For Standard Fields
- Use camelCase: `firstName`, `accountId`
- Be descriptive: `dateCreated` not `date1`
- Follow Neon CRM conventions

### For Custom Fields
- Use clear prefixes: `V-` for volunteer fields
- Be specific but not overly long
- Use consistent terminology across organization
- Avoid abbreviations where possible

### For Migration Targets
- Prefer broader, more inclusive field names
- Use standard organizational terminology
- Consider future scalability
- Maintain consistency with existing schema

## Testing Field Names

When writing tests or examples, use these realistic field names:

### Valid Field Names (for positive tests)
- `firstName`
- `lastName`
- `email1`
- `V-Volunteer Skills`
- `V-Volunteer Interests`

### Invalid Field Names (for negative tests)
- `NonExistentField`
- `InvalidField123`
- `Missing-Field`

This ensures tests are realistic and demonstrate actual usage patterns.

## Best Practices

1. **Consistency**: Use the same field names across all documentation
2. **Reality**: Use field names that actually exist in typical Neon CRM setups
3. **Clarity**: Choose field names that clearly communicate their purpose
4. **Future-proofing**: Avoid overly specific names that may become outdated
5. **Organization**: Group related fields logically

## Updates and Maintenance

This document should be updated when:
- New standard field names are identified
- V-field patterns change in common usage
- Migration patterns evolve
- New field types are introduced

Last Updated: 2025-01-09
