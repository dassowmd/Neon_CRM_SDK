# Claude System Prompt for Neon CRM SDK Development

## 🛡️ CRITICAL SAFETY INSTRUCTIONS

### ❌ ABSOLUTE PROHIBITIONS:
1. **DO NOT** execute any code that creates, updates, or deletes database records
2. **DO NOT** run account creation, donation, membership, or event creation operations
3. **DO NOT** run any code that makes write operations to the Neon CRM database
4. **DO NOT** execute any examples marked as "creation" or "CRUD" operations
5. **DO NOT** trust existing tests - they were not in a solid state when created
6. **DO NOT** run validation with `validate=True` if it might cause timeouts

### ✅ PERMITTED ACTIONS:
- Read and analyze existing code
- Update field mappings, type definitions, and configuration files
- Fix syntax errors, import statements, and documentation
- Run READ-ONLY search operations with small page sizes (`pageSize <= 5`)
- Use `validate=False` for testing to avoid timeout issues
- Create documentation, analysis, and development notes

## 📋 DEVELOPMENT CONTEXT

### Primary Resources:
- **Swagger Specification**: `neon-api-v2.10.yaml` (source of truth for API structure)
- **MCP Configuration**: `.swagger-mcp` (configured for Swagger MCP tools)
- **Development Notes**: `CLAUDE_DEVELOPMENT_NOTES.md` (context from previous sessions)
- **Todo List**: `todo.md` (current priorities and issues)

### Known Critical Issues:
1. **Field Name Format**: API expects "Display Name" format (e.g., "First Name") but SDK converts to camelCase (e.g., "firstName")
2. **Search vs List**: Some resources (like campaigns) only support `.list()`, not `.search()`
3. **Field Validation Errors**: HTTP 400 "Search key is invalid" throughout examples
4. **Enum Values**: Use "INDIVIDUAL" (all caps), not "Individual" for account types

### Current Status:
- Field mapping temporarily disabled in `src/neon_crm/resources/base.py` line 586
- 24 out of 35 files have been fixed with automated script
- Examples and analysis directories need field name corrections
- Types and enums need updates from Swagger specification

## 🔧 DEVELOPMENT APPROACH

### Code Analysis Priority:
1. **Read before modifying** - Always understand existing code first
2. **Use Swagger as truth** - When in doubt, check `neon-api-v2.10.yaml`
3. **Test minimally** - Small page sizes, read-only operations only
4. **Document changes** - Update relevant files when making fixes

### Field Name Guidelines:
```python
# ❌ WRONG (camelCase)
{"field": "firstName", "operator": "EQUAL", "value": "John"}

# ✅ CORRECT (Display Name format)
{"field": "First Name", "operator": "EQUAL", "value": "John"}
```

### Safe Testing Pattern:
```python
# Safe search with minimal impact
search_request = {
    "searchFields": [{"field": "Account Type", "operator": "EQUAL", "value": "INDIVIDUAL"}],
    "outputFields": ["Account ID", "First Name", "Last Name"],
    "pagination": {"currentPage": 0, "pageSize": 3}
}
results = list(client.accounts.search(search_request, validate=False))
```

## 🛠️ AVAILABLE TOOLS

### MCP Tools (Pre-configured):
- `mcp__swagger-mcp__listEndpoints` - List all API endpoints
- `mcp__swagger-mcp__generateEndpointToolCode` - Generate TypeScript for endpoints
- `mcp__swagger-mcp__generateModelCode` - Generate model code from Swagger
- `mcp__github__*` - GitHub operations (if needed)

### File Locations:
- **Core SDK**: `src/neon_crm/` directory
- **Examples**: `examples/` directory (many need field fixes)
- **Analysis**: `analysis/` directory (field inconsistencies)
- **Tests**: `tests/` directory (don't trust, were incomplete)

## 📝 EXPECTED WORKFLOW

1. **Read context files** (`CLAUDE_DEVELOPMENT_NOTES.md`, `todo.md`)
2. **Identify specific issue** to work on from todo list
3. **Analyze relevant code** before making changes
4. **Use Swagger MCP tools** to verify API structure when needed
5. **Make minimal, targeted fixes** to address specific issues
6. **Test read-only operations** with small limits if necessary
7. **Update documentation** and todo list with progress
8. **Use TodoWrite tool** to track progress throughout session

## 🎯 CURRENT PRIORITIES

1. **Fix field validation errors** in account_retrieval.ipynb
2. **Update types and enums** from Swagger specification
3. **Review all examples** for field name issues (analysis only)
4. **Improve error messages** with field suggestions
5. **Document field name requirements** for users

## ⚠️ IMPORTANT REMINDERS

- **This is a production CRM system** - any write operations could affect real data
- **Examples connect to live database** - only run read operations with small limits
- **Field mapping was broken** - API uses display names, not camelCase
- **Validation can timeout** - use `validate=False` during development
- **Always check Swagger spec** - it's more reliable than existing code comments

---

**Session Goal**: Fix SDK issues while maintaining absolute safety regarding database operations.
**Success Criteria**: Code improvements without any risk of data modification.
**Emergency Stop**: If any operation might modify data, stop immediately and document the concern.
