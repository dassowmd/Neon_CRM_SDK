# Custom Field Name to ID Conversion Enhancement

## Overview

This enhancement allows users to use custom field names instead of integer IDs in search requests. The system automatically converts custom field names to their appropriate ID format by validating against the cache.

## Key Features

1. **Automatic Field Name Resolution**: Use friendly custom field names instead of remembering integer IDs
2. **Cache-Based Validation**: Leverages existing custom field caching for performance
3. **Backward Compatibility**: Existing integer ID usage continues to work unchanged
4. **Smart Conversion**:
   - Search fields: custom field ID as string (API requirement)
   - Output fields: custom field ID as integer (API requirement)

## Usage Examples

### Before Enhancement
```python
# Had to remember/lookup custom field IDs
search_request = {
    "searchFields": [
        {"field": "123", "operator": "EQUAL", "value": "volunteer"}  # Hard to remember
    ],
    "outputFields": ["firstName", "lastName", 456]  # What is field 456?
}

results = client.accounts.search(search_request)
```

### After Enhancement
```python
# Use friendly field names - much more readable!
search_request = {
    "searchFields": [
        {"field": "V-Volunteer Skills", "operator": "EQUAL", "value": "canvassing"}
    ],
    "outputFields": ["firstName", "lastName", "Custom Notes"]
}

results = client.accounts.search(search_request)
```

## How It Works

1. **Smart Field Detection**: The system efficiently identifies which fields need conversion:
   - ✅ Processes: `"V-Volunteer Skills"`, `"Custom Notes"`, `"DPW ID"` (actual custom field names)
   - ⏭️ Skips: `123` (integer ID), `"456"` (string digit ID - already converted)
   - ⏭️ Skips: `"firstName"`, `"lastName"`, `"Account ID"` (standard fields - detected early, no custom field lookup)

2. **Optimized Validation Process**:
   - **Step 1**: Check if field is already an ID (integer or digit string) → Skip
   - **Step 2**: Check if field is a standard field → Skip (no custom field lookup needed!)
   - **Step 3**: Only then check custom fields cache via `find_by_name_and_category()`

3. **ID Conversion**:
   - Found custom fields → converted to their integer IDs
   - Search fields get string representation: `"123"`
   - Output fields get integer representation: `123`

4. **Performance Benefits**:
   - **No unnecessary API calls** for standard fields like "First Name", "Last Name"
   - **No confusing log messages** asking "Did you mean..." for obvious standard fields
   - **Faster processing** by avoiding custom field lookups for known standard fields

## Implementation Details

### New Methods

#### `_is_standard_field()`
```python
def _is_standard_field(self, field_name: str) -> bool:
    """Check if a field name is a standard field for this resource."""
    # Uses get_output_fields() to check against standardFields
    # Prevents unnecessary custom field lookups
    # Gracefully handles errors if field discovery fails
```

#### `_convert_field_names_to_ids()`
```python
def _convert_field_names_to_ids(self, search_request: SearchRequest) -> SearchRequest:
    """Convert custom field names to their integer IDs in search and output fields."""
    # Step 1: Skip integer IDs and digit strings
    # Step 2: Skip standard fields (using _is_standard_field)
    # Step 3: Only then check custom fields cache
    # Maintains backward compatibility with existing integer IDs
```

### Integration with Search Request Preparation

The conversion happens early in the `_prepare_search_request()` pipeline:

1. **Field name conversion** ← NEW
2. Type conversions (integers to strings for search, etc.)
3. Wildcard output field expansion
4. Validation (if enabled)

## Error Handling

- **Unknown Fields**: Field names not found in cache are left unchanged
- **No Category Mapping**: Resources without custom field support skip conversion
- **Graceful Degradation**: Errors in custom field lookup don't break the search

## Testing

Comprehensive test coverage includes:

- ✅ Search field name conversion
- ✅ Output field name conversion
- ✅ Field not found scenarios
- ✅ No category mapping scenarios
- ✅ Integration with existing search preparation
- ✅ Backward compatibility with integer IDs

## Benefits

1. **Developer Experience**: More readable and maintainable code
2. **Reduced Errors**: No need to memorize or lookup field IDs
3. **Performance**: Leverages existing caching infrastructure
4. **Compatibility**: Works seamlessly with existing code
5. **Validation**: Ensures fields exist before making API calls
