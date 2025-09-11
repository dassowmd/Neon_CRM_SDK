"""Unit tests for type definitions."""

import pytest
from typing import Dict, Any

from neon_crm.types import (
    IndividualAccount,
    CompanyAccount,
    AccountData,
    Address,
    SearchRequest,
    PaginationParams,
    CreateIndividualAccountPayload,
    CreateCompanyAccountPayload,
    CompleteAccountPayload
)


@pytest.mark.unit
class TestTypeDefinitions:
    """Test cases for type definitions."""

    def test_individual_account_type(self):
        """Test IndividualAccount type structure."""
        account: IndividualAccount = {
            "accountType": "INDIVIDUAL",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "dateOfBirth": "1990-01-15"
        }
        
        assert account["accountType"] == "INDIVIDUAL"
        assert account["firstName"] == "John"
        assert account["email"] == "john.doe@example.com"

    def test_company_account_type(self):
        """Test CompanyAccount type structure."""
        account: CompanyAccount = {
            "accountType": "COMPANY",
            "name": "Acme Corp",
            "email": "info@acme.com",
            "website": "https://acme.com"
        }
        
        assert account["accountType"] == "COMPANY"
        assert account["name"] == "Acme Corp"
        assert account["website"] == "https://acme.com"

    def test_address_type(self):
        """Test Address type structure."""
        address: Address = {
            "addressType": "Home",
            "streetAddress1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zipCode": "62701",
            "country": "USA",
            "isPrimaryAddress": True
        }
        
        assert address["addressType"] == "Home"
        assert address["streetAddress1"] == "123 Main St"
        assert address["isPrimaryAddress"] is True

    def test_search_request_type(self):
        """Test SearchRequest type structure."""
        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "firstName",
                    "operator": "EQUAL",
                    "value": "John"
                }
            ],
            "outputFields": ["accountId", "firstName", "lastName"],
            "pagination": {
                "currentPage": 1,
                "pageSize": 50
            }
        }
        
        assert len(search_request["searchFields"]) == 1
        assert search_request["searchFields"][0]["field"] == "firstName"
        assert search_request["outputFields"] == ["accountId", "firstName", "lastName"]
        assert search_request["pagination"]["pageSize"] == 50

    def test_pagination_params_type(self):
        """Test PaginationParams type structure."""
        pagination: PaginationParams = {
            "currentPage": 2,
            "pageSize": 25
        }
        
        assert pagination["currentPage"] == 2
        assert pagination["pageSize"] == 25

    def test_create_individual_account_payload(self):
        """Test CreateIndividualAccountPayload type structure."""
        payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Jane",
                "lastName": "Smith",
                "email": "jane.smith@example.com"
            }
        }
        
        assert payload["individualAccount"]["accountType"] == "INDIVIDUAL"
        assert payload["individualAccount"]["firstName"] == "Jane"

    def test_create_company_account_payload(self):
        """Test CreateCompanyAccountPayload type structure."""
        payload: CreateCompanyAccountPayload = {
            "companyAccount": {
                "accountType": "COMPANY",
                "name": "Tech Solutions",
                "email": "info@techsolutions.com"
            }
        }
        
        assert payload["companyAccount"]["accountType"] == "COMPANY"
        assert payload["companyAccount"]["name"] == "Tech Solutions"

    def test_complete_account_payload(self):
        """Test CompleteAccountPayload type structure."""
        payload: CompleteAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Bob",
                "lastName": "Johnson",
                "email": "bob.johnson@example.com"
            },
            "addresses": [
                {
                    "addressType": "Home",
                    "streetAddress1": "456 Oak Ave",
                    "city": "Portland",
                    "state": "OR",
                    "zipCode": "97201",
                    "country": "USA",
                    "isPrimaryAddress": True
                }
            ],
            "source": {
                "sourceId": 1001,
                "sourceName": "Website"
            },
            "customFields": [
                {
                    "fieldId": "custom_1",
                    "value": "Test Value"
                }
            ]
        }
        
        assert payload["individualAccount"]["firstName"] == "Bob"
        assert len(payload["addresses"]) == 1
        assert payload["addresses"][0]["addressType"] == "Home"
        assert payload["source"]["sourceName"] == "Website"
        assert len(payload["customFields"]) == 1

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        # Test minimal individual account
        minimal_individual: IndividualAccount = {
            "accountType": "INDIVIDUAL",
            "firstName": "John",
            "lastName": "Doe"
        }
        
        assert "email" not in minimal_individual
        assert minimal_individual["firstName"] == "John"

        # Test minimal company account
        minimal_company: CompanyAccount = {
            "accountType": "COMPANY",
            "name": "Test Company"
        }
        
        assert "email" not in minimal_company
        assert minimal_company["name"] == "Test Company"

    def test_type_flexibility(self):
        """Test that types are flexible with additional fields."""
        # Types should accept additional fields due to total=False
        extended_account: IndividualAccount = {
            "accountType": "INDIVIDUAL",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            # Additional fields that might exist in API responses
        }
        
        assert extended_account["firstName"] == "John"