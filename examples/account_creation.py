"""
Examples of creating accounts with the Neon CRM SDK.

This file demonstrates various ways to create individual and company accounts
with different levels of detail and optional fields.
"""

from neon_crm import NeonClient
from neon_crm.types import (
    Address,
    CompanyAccount,
    CompleteAccountPayload,
    CreateCompanyAccountPayload,
    CreateIndividualAccountPayload,
    IndividualAccount,
    Source,
    Timestamps,
)


def create_basic_individual_account():
    """Create a basic individual account with minimal required fields."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Minimal individual account - just the required fields
    payload: CreateIndividualAccountPayload = {
        "individualAccount": {
            "accountType": "INDIVIDUAL",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
        }
    }

    try:
        response = client.accounts.create(payload)
        print(f"Created individual account: {response['accountId']}")
        return response
    except Exception as e:
        print(f"Error creating account: {e}")


def create_detailed_individual_account():
    """Create an individual account with comprehensive details."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Comprehensive individual account with all optional fields
    individual_account: IndividualAccount = {
        "accountType": "INDIVIDUAL",
        "firstName": "Jane",
        "lastName": "Smith",
        "middleName": "Marie",
        "prefix": "Dr.",
        "suffix": "PhD",
        "salutation": "Dr. Smith",
        "preferredName": "Janey",
        "email": "jane.smith@example.com",
        "phone": "+1-555-123-4567",
        "website": "https://janesmith.com",
        "jobTitle": "Research Scientist",
        "gender": "Female",
        "dateOfBirth": "1985-03-15",
        "deceased": False,
        # Multiple contact methods
        "email1": "jane.smith@example.com",
        "email2": "j.smith@work.com",
        "phone1": "+1-555-123-4567",
        "phone1Type": "Mobile",
        "phone2": "+1-555-987-6543",
        "phone2Type": "Work",
        "fax": "+1-555-123-4568",
    }

    # Address information
    address: Address = {
        "addressType": "Home",
        "streetAddress1": "123 Main Street",
        "streetAddress2": "Apt 4B",
        "city": "Anytown",
        "state": "CA",
        "zipCode": "12345",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    # Source tracking
    source: Source = {"sourceId": 1001, "sourceName": "Website Contact Form"}

    # Custom timestamps
    timestamps: Timestamps = {"createdDateTime": "2024-01-15T10:30:00Z"}

    # Complete payload with all optional sections
    payload: CompleteAccountPayload = {
        "individualAccount": individual_account,
        "addresses": [address],
        "source": source,
        "timestamps": timestamps,
        "loginName": "janesmith",
        "consent": {"emailOptIn": True, "mailOptIn": False, "phoneOptIn": True},
        "customFields": [{"fieldId": "custom_field_1", "value": "Premium Member"}],
    }

    try:
        response = client.accounts.create(payload)
        print(f"Created detailed individual account: {response['accountId']}")
        return response
    except Exception as e:
        print(f"Error creating detailed account: {e}")


def create_basic_company_account():
    """Create a basic company account with minimal required fields."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Minimal company account
    payload: CreateCompanyAccountPayload = {
        "companyAccount": {
            "accountType": "COMPANY",
            "name": "Acme Corporation",
            "email": "info@acme.com",
        }
    }

    try:
        response = client.accounts.create(payload)
        print(f"Created company account: {response['accountId']}")
        return response
    except Exception as e:
        print(f"Error creating company account: {e}")


def create_detailed_company_account():
    """Create a company account with comprehensive details."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Comprehensive company account
    company_account: CompanyAccount = {
        "accountType": "COMPANY",
        "name": "Tech Solutions Inc.",
        "companyName": "Tech Solutions Inc.",
        "organizationType": "Corporation",
        "email": "contact@techsolutions.com",
        "phone": "+1-555-TECH-SOL",
        "website": "https://techsolutions.com",
        "fax": "+1-555-TECH-FAX",
        # Multiple contact methods
        "email1": "contact@techsolutions.com",
        "email2": "sales@techsolutions.com",
        "email3": "support@techsolutions.com",
        "phone1": "+1-555-TECH-SOL",
        "phone1Type": "Main",
        "phone2": "+1-555-TECH-SALE",
        "phone2Type": "Sales",
        "phone3": "+1-555-TECH-HELP",
        "phone3Type": "Support",
    }

    # Company address
    address: Address = {
        "addressType": "Business",
        "streetAddress1": "456 Business Blvd",
        "streetAddress2": "Suite 100",
        "city": "Business City",
        "state": "NY",
        "zipCode": "54321",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    # Source tracking
    source: Source = {"sourceId": 2001, "sourceName": "Trade Show Lead"}

    # Complete company payload
    payload: CompleteAccountPayload = {
        "companyAccount": company_account,
        "addresses": [address],
        "source": source,
        "consent": {"emailOptIn": True, "mailOptIn": True, "phoneOptIn": False},
        "customFields": [
            {"fieldId": "industry_type", "value": "Technology"},
            {"fieldId": "annual_revenue", "value": "1000000"},
        ],
    }

    try:
        response = client.accounts.create(payload)
        print(f"Created detailed company account: {response['accountId']}")
        return response
    except Exception as e:
        print(f"Error creating detailed company account: {e}")


def create_account_with_multiple_addresses():
    """Create an account with multiple addresses."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Individual with multiple addresses
    individual_account: IndividualAccount = {
        "accountType": "INDIVIDUAL",
        "firstName": "Michael",
        "lastName": "Johnson",
        "email": "michael.johnson@example.com",
        "phone": "+1-555-246-8135",
    }

    # Multiple addresses
    home_address: Address = {
        "addressType": "Home",
        "streetAddress1": "789 Residential St",
        "city": "Hometown",
        "state": "TX",
        "zipCode": "78901",
        "country": "USA",
        "isPrimaryAddress": True,
    }

    work_address: Address = {
        "addressType": "Work",
        "streetAddress1": "321 Corporate Ave",
        "streetAddress2": "Floor 15",
        "city": "Business District",
        "state": "TX",
        "zipCode": "78902",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    billing_address: Address = {
        "addressType": "Billing",
        "streetAddress1": "PO Box 12345",
        "city": "Mail Center",
        "state": "TX",
        "zipCode": "78903",
        "country": "USA",
        "isPrimaryAddress": False,
    }

    payload: CompleteAccountPayload = {
        "individualAccount": individual_account,
        "addresses": [home_address, work_address, billing_address],
    }

    try:
        response = client.accounts.create(payload)
        print(f"Created account with multiple addresses: {response['accountId']}")
        return response
    except Exception as e:
        print(f"Error creating account with multiple addresses: {e}")


if __name__ == "__main__":
    print("Neon CRM SDK - Account Creation Examples")
    print("=" * 50)

    # Note: Replace with your actual credentials
    print("Note: Update the org_id and api_key with your actual credentials")
    print("      and set the appropriate environment (production/trial)")
    print()

    # Uncomment the examples you want to run:

    # print("Creating basic individual account...")
    # create_basic_individual_account()

    # print("\nCreating detailed individual account...")
    # create_detailed_individual_account()

    # print("\nCreating basic company account...")
    # create_basic_company_account()

    # print("\nCreating detailed company account...")
    # create_detailed_company_account()

    # print("\nCreating account with multiple addresses...")
    # create_account_with_multiple_addresses()

    print(
        "Examples ready to run. Uncomment the desired examples and add your credentials."
    )
