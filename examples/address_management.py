"""
Examples of managing addresses with the Neon CRM SDK.

This file demonstrates how to create accounts with addresses,
update address information, and manage multiple addresses per account.
"""

from neon_crm import NeonClient
from neon_crm.types import (
    Address,
    CompanyAccount,
    CompleteAccountPayload,
    IndividualAccount,
)


def create_account_with_single_address():
    """Create an account with a single address."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Creating account with single address...")

    # Individual account with home address
    individual_account: IndividualAccount = {
        "accountType": "INDIVIDUAL",
        "firstName": "Sarah",
        "lastName": "Johnson",
        "email": "sarah.johnson@example.com",
        "phone": "+1-555-234-5678",
    }

    # Home address
    home_address: Address = {
        "addressType": "Home",
        "streetAddress1": "123 Maple Street",
        "streetAddress2": "Unit 2A",
        "city": "Springfield",
        "state": "IL",
        "zipCode": "62701",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    payload: CompleteAccountPayload = {
        "individualAccount": individual_account,
        "addresses": [home_address],
    }

    try:
        response = client.accounts.create(payload)
        account_id = response.get("accountId")
        print(f"✓ Created account {account_id} with home address")
        return account_id

    except Exception as e:
        print(f"✗ Error creating account with address: {e}")
        return None


def create_account_with_multiple_addresses():
    """Create an account with multiple addresses."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Creating account with multiple addresses...")

    # Individual account
    individual_account: IndividualAccount = {
        "accountType": "INDIVIDUAL",
        "firstName": "David",
        "lastName": "Chen",
        "email": "david.chen@example.com",
        "phone": "+1-555-345-6789",
    }

    # Home address (primary)
    home_address: Address = {
        "addressType": "Home",
        "streetAddress1": "456 Oak Avenue",
        "city": "Portland",
        "state": "OR",
        "zipCode": "97201",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    # Work address
    work_address: Address = {
        "addressType": "Work",
        "streetAddress1": "789 Business Plaza",
        "streetAddress2": "Suite 300",
        "city": "Portland",
        "state": "OR",
        "zipCode": "97204",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    # Mailing address (different from home/work)
    mailing_address: Address = {
        "addressType": "Mailing",
        "streetAddress1": "PO Box 567",
        "city": "Portland",
        "state": "OR",
        "zipCode": "97208",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    payload: CompleteAccountPayload = {
        "individualAccount": individual_account,
        "addresses": [home_address, work_address, mailing_address],
    }

    try:
        response = client.accounts.create(payload)
        account_id = response.get("accountId")
        print(f"✓ Created account {account_id} with 3 addresses:")
        print(f"  - Home: {home_address['streetAddress1']}, {home_address['city']}")
        print(f"  - Work: {work_address['streetAddress1']}, {work_address['city']}")
        print(
            f"  - Mailing: {mailing_address['streetAddress1']}, {mailing_address['city']}"
        )
        return account_id

    except Exception as e:
        print(f"✗ Error creating account with multiple addresses: {e}")
        return None


def create_company_with_addresses():
    """Create a company account with business addresses."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Creating company with business addresses...")

    # Company account
    company_account: CompanyAccount = {
        "accountType": "COMPANY",
        "name": "Green Valley Consulting",
        "companyName": "Green Valley Consulting LLC",
        "organizationType": "LLC",
        "email": "info@greenvalley.com",
        "phone": "+1-555-456-7890",
        "website": "https://greenvalley.com",
    }

    # Main business address
    business_address: Address = {
        "addressType": "Business",
        "streetAddress1": "1000 Corporate Drive",
        "streetAddress2": "Building A",
        "city": "Denver",
        "state": "CO",
        "zipCode": "80202",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    # Billing address (different from main location)
    billing_address: Address = {
        "addressType": "Billing",
        "streetAddress1": "PO Box 12345",
        "city": "Denver",
        "state": "CO",
        "zipCode": "80201",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    # Shipping/receiving address
    shipping_address: Address = {
        "addressType": "Shipping",
        "streetAddress1": "500 Warehouse Lane",
        "city": "Commerce City",
        "state": "CO",
        "zipCode": "80022",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    payload: CompleteAccountPayload = {
        "companyAccount": company_account,
        "addresses": [business_address, billing_address, shipping_address],
    }

    try:
        response = client.accounts.create(payload)
        account_id = response.get("accountId")
        print(f"✓ Created company {account_id} with business addresses:")
        print(
            f"  - Business: {business_address['streetAddress1']}, {business_address['city']}"
        )
        print(
            f"  - Billing: {billing_address['streetAddress1']}, {billing_address['city']}"
        )
        print(
            f"  - Shipping: {shipping_address['streetAddress1']}, {shipping_address['city']}"
        )
        return account_id

    except Exception as e:
        print(f"✗ Error creating company with addresses: {e}")
        return None


def update_account_with_new_address():
    """Update an existing account to add a new address."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # This would typically be an existing account ID
    account_id = "12345"  # Replace with actual account ID

    print(f"Adding new address to existing account {account_id}...")

    try:
        # First, get the current account data
        current_account = client.accounts.get(account_id)
        print(
            f"Current account: {current_account.get('firstName')} {current_account.get('lastName')}"
        )

        # Create the new address to add
        vacation_address: Address = {
            "addressType": "Vacation",
            "streetAddress1": "789 Beach Road",
            "city": "Myrtle Beach",
            "state": "SC",
            "zipCode": "29577",
            "country": "USA",
            "isPrimaryAddress": False,
        }

        # Prepare update payload
        # Note: In practice, you'd need to include existing addresses to avoid overwriting
        update_data = {
            "addresses": [vacation_address]  # This would replace all addresses
        }

        # Use PATCH to partially update
        response = client.accounts.patch(account_id, update_data)
        print(f"✓ Added vacation address to account {account_id}")
        return response

    except Exception as e:
        print(f"✗ Error updating account with new address: {e}")
        return None


def international_address_example():
    """Create account with international address."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Creating account with international address...")

    # Individual account
    individual_account: IndividualAccount = {
        "accountType": "INDIVIDUAL",
        "firstName": "Emma",
        "lastName": "Thompson",
        "email": "emma.thompson@example.co.uk",
        "phone": "+44-20-1234-5678",
    }

    # UK address
    uk_address: Address = {
        "addressType": "Home",
        "streetAddress1": "42 Baker Street",
        "streetAddress2": "Flat 3B",
        "city": "London",
        "state": "England",  # Or could be county/region
        "zipCode": "NW1 6XE",
        "postalCode": "NW1 6XE",  # Alternative field name
        "country": "United Kingdom",
        "isPrimaryAddress": True,
    }

    payload: CompleteAccountPayload = {
        "individualAccount": individual_account,
        "addresses": [uk_address],
    }

    try:
        response = client.accounts.create(payload)
        account_id = response.get("accountId")
        print(f"✓ Created UK account {account_id}")
        print(
            f"  Address: {uk_address['streetAddress1']}, {uk_address['city']}, {uk_address['country']}"
        )
        return account_id

    except Exception as e:
        print(f"✗ Error creating international account: {e}")
        return None


def address_validation_example():
    """Example showing address validation and best practices."""
    print("Address Validation and Best Practices")
    print("=" * 40)

    def validate_address(address: Address) -> bool:
        """Basic address validation."""
        required_fields = ["addressType", "streetAddress1", "city", "country"]

        for field in required_fields:
            if not address.get(field):
                print(f"✗ Missing required field: {field}")
                return False

        # Check address type
        valid_types = [
            "Home",
            "Work",
            "Business",
            "Mailing",
            "Billing",
            "Shipping",
            "Vacation",
        ]
        if address["addressType"] not in valid_types:
            print(f"✗ Invalid address type: {address['addressType']}")
            print(f"  Valid types: {', '.join(valid_types)}")
            return False

        # US-specific validation
        if address.get("country") in ["USA", "United States", "US"]:
            if not address.get("state"):
                print("✗ State required for US addresses")
                return False
            if not address.get("zipCode"):
                print("✗ ZIP code required for US addresses")
                return False

        print(f"✓ Address validation passed for {address['addressType']} address")
        return True

    # Test addresses
    valid_address: Address = {
        "addressType": "Home",
        "streetAddress1": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zipCode": "12345",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    invalid_address: Address = {
        "addressType": "InvalidType",  # Invalid type
        "streetAddress1": "456 Oak St",
        # Missing city, state, zip
        "country": "USA",
    }

    print("Testing valid address:")
    validate_address(valid_address)

    print("\nTesting invalid address:")
    validate_address(invalid_address)


def address_formatting_examples():
    """Examples of proper address formatting for different regions."""
    print("\nAddress Formatting Examples")
    print("=" * 30)

    # US Address
    us_address: Address = {
        "addressType": "Home",
        "streetAddress1": "123 Main Street",
        "streetAddress2": "Apt 4B",  # Optional
        "city": "Springfield",
        "state": "IL",  # Use 2-letter state code
        "zipCode": "62701",  # 5-digit or 9-digit (62701-1234)
        "country": "USA",
        "isPrimaryAddress": True,
    }
    print("US Address Format:")
    print(f"  {us_address['streetAddress1']}")
    if us_address.get("streetAddress2"):
        print(f"  {us_address['streetAddress2']}")
    print(f"  {us_address['city']}, {us_address['state']} {us_address['zipCode']}")
    print(f"  {us_address['country']}")

    # Canadian Address
    canada_address: Address = {
        "addressType": "Home",
        "streetAddress1": "456 Maple Avenue",
        "city": "Toronto",
        "state": "ON",  # Province code
        "zipCode": "M5V 3A8",  # Canadian postal code format
        "country": "Canada",
        "isPrimaryAddress": True,
    }
    print("\nCanadian Address Format:")
    print(f"  {canada_address['streetAddress1']}")
    print(
        f"  {canada_address['city']}, {canada_address['state']} {canada_address['zipCode']}"
    )
    print(f"  {canada_address['country']}")

    # UK Address
    uk_address: Address = {
        "addressType": "Home",
        "streetAddress1": "42 Baker Street",
        "streetAddress2": "Flat 3B",
        "city": "London",
        "state": "England",  # Country within UK
        "zipCode": "NW1 6XE",  # UK postcode
        "country": "United Kingdom",
        "isPrimaryAddress": True,
    }
    print("\nUK Address Format:")
    print(f"  {uk_address['streetAddress1']}")
    if uk_address.get("streetAddress2"):
        print(f"  {uk_address['streetAddress2']}")
    print(f"  {uk_address['city']}")
    print(f"  {uk_address['state']}")
    print(f"  {uk_address['zipCode']}")
    print(f"  {uk_address['country']}")


if __name__ == "__main__":
    print("Neon CRM SDK - Address Management Examples")
    print("=" * 50)

    # Note: Replace with your actual credentials and account IDs
    print("Note: Update the org_id and api_key with your actual credentials")
    print("      Update account_id variables with real account IDs from your system")
    print("      Set the appropriate environment (production/trial)")
    print()

    # Address validation and formatting (no API calls)
    address_validation_example()
    address_formatting_examples()

    # Uncomment the examples you want to run:

    # print("\n" + "="*50)
    # create_account_with_single_address()

    # print("\n" + "="*50)
    # create_account_with_multiple_addresses()

    # print("\n" + "="*50)
    # create_company_with_addresses()

    # print("\n" + "="*50)
    # update_account_with_new_address()

    # print("\n" + "="*50)
    # international_address_example()

    print(
        "\nExamples ready to run. Uncomment the desired examples and add your credentials."
    )
