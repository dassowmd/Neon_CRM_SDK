# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-09-10

### Added
- Initial release of the Neon CRM Python SDK
- Full support for Neon CRM API v2.10
- Comprehensive resource coverage (33+ API resource categories)
- Type-safe implementation with Pydantic models
- Synchronous and asynchronous client support
- Automatic pagination for list operations
- Advanced search functionality for supported resources
- Built-in error handling with specific exception types
- Rate limiting and retry mechanisms
- Comprehensive test suite
- Usage examples and documentation
- Support for both production and trial environments
- Environment variable configuration support

### Resources Included
- Accounts (with contact management)
- Donations
- Events (legacy events)
- Memberships
- Activities
- Campaigns
- Custom Fields & Objects
- Grants
- Households
- Online Store & Orders
- Payments & Pledges
- Recurring Donations
- Soft Credits
- Volunteers (full volunteer management)
- Webhooks
- And more...

### Features
- HTTP Basic Authentication with organization ID and API key
- Automatic API version header management
- Context manager support for proper resource cleanup
- Flexible search with dynamic field selection
- Relationship management between resources
- Comprehensive error handling and validation
- Full type hints for better IDE support
