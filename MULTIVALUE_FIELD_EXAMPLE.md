# Multi-Value Custom Field Management Example

## Scenario
You have a MultiSelect custom field "V-Volunteer Skills" with current values:
- "Familiar with Word"
- "Writing"

You want to add "Technology" without duplicating existing values.

## Implementation

### 1. Using Field Names (New Enhancement)

```python
# Get current account data using field names
search_request = {
    "searchFields": [
        {"field": "Account ID", "operator": "EQUAL", "value": "12345"}
    ],
    "outputFields": ["firstName", "lastName", "V-Volunteer Skills"]
}

accounts = list(client.accounts.search(search_request))
account = accounts[0] if accounts else None

if account:
    # Get current custom field value (will be converted from ID automatically)
    current_skills = account.get("V-Volunteer Skills", "")

    # Parse existing skills (comma-separated)
    if current_skills:
        skills_list = [skill.strip() for skill in current_skills.split(",")]
    else:
        skills_list = []

    # Add new skill if not already present
    new_skill = "Technology"
    if new_skill not in skills_list:
        skills_list.append(new_skill)

        # Update the account with new skills
        updated_skills = ", ".join(skills_list)

        # Update using field name (will be converted to ID automatically)
        update_data = {
            "V-Volunteer Skills": updated_skills
        }

        client.accounts.update(account["Account ID"], update_data)
        print(f"Added '{new_skill}' to volunteer skills")
    else:
        print(f"'{new_skill}' already exists in volunteer skills")
```

### 2. Helper Function for Multi-Value Field Management

```python
def add_multiselect_value(client, account_id: str, field_name: str, new_value: str) -> bool:
    """
    Add a value to a MultiSelect custom field if it doesn't already exist.

    Args:
        client: Neon CRM client
        account_id: Account ID to update
        field_name: Custom field name (e.g., "V-Volunteer Skills")
        new_value: Value to add

    Returns:
        True if value was added, False if it already existed
    """
    # Get current account data
    search_request = {
        "searchFields": [
            {"field": "Account ID", "operator": "EQUAL", "value": account_id}
        ],
        "outputFields": ["Account ID", field_name]
    }

    accounts = list(client.accounts.search(search_request))
    if not accounts:
        raise ValueError(f"Account {account_id} not found")

    account = accounts[0]
    current_value = account.get(field_name, "")

    # Parse existing values
    if current_value:
        values_list = [value.strip() for value in current_value.split(",")]
    else:
        values_list = []

    # Check if value already exists (case-insensitive)
    if any(existing.lower() == new_value.lower() for existing in values_list):
        return False  # Value already exists

    # Add new value and update
    values_list.append(new_value)
    updated_value = ", ".join(values_list)

    update_data = {field_name: updated_value}
    client.accounts.update(account_id, update_data)

    return True  # Value was added

# Usage
if add_multiselect_value(client, "12345", "V-Volunteer Skills", "Technology"):
    print("Technology added to volunteer skills")
else:
    print("Technology already exists in volunteer skills")
```

### 3. Validation Enhancement

For comprehensive validation, you could also enhance the search field validation:

```python
def validate_multiselect_addition(client, field_name: str, new_value: str, existing_values: str = None) -> dict:
    """
    Validate adding a value to a MultiSelect field.

    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "warnings": [],
        "errors": []
    }

    if not new_value or not new_value.strip():
        result["valid"] = False
        result["errors"].append("New value cannot be empty")
        return result

    new_value = new_value.strip()

    if existing_values:
        existing_list = [v.strip().lower() for v in existing_values.split(",")]
        if new_value.lower() in existing_list:
            result["warnings"].append(f"Value '{new_value}' already exists")

    # Additional validation could check against valid options
    # if the custom field has predefined options

    return result
```

## Key Benefits of Field Name Enhancement

1. **Readable Code**: Use `"V-Volunteer Skills"` instead of remembering custom field ID
2. **No API Lookup Overhead**: Standard fields like `"Account ID"` are detected and skip custom field lookup
3. **Automatic Conversion**: Field names are automatically converted to appropriate ID format
4. **Backward Compatible**: Existing code using IDs continues to work

## MultiSelect Field Considerations

- Values are stored as comma-separated strings
- Case sensitivity matters for duplicate detection
- Leading/trailing spaces should be trimmed
- Consider maximum length limits for the combined string
- Some MultiSelect fields may have predefined valid options
