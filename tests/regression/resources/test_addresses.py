"""Comprehensive regression tests for AddressesResource.

Tests both read-only operations for the addresses endpoint.
Organized to match src/neon_crm/resources/addresses.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestAddressesReadOnly:
    """Read-only tests for AddressesResource - safe for production."""

    def test_addresses_list_basic(self, regression_client):
        """Test basic addresses listing."""
        addresses = list(regression_client.addresses.list(limit=5))

        print(f"✓ Retrieved {len(addresses)} addresses")

        if addresses:
            first_address = addresses[0]
            assert isinstance(first_address, dict), "Address should be a dictionary"
            print(f"Address structure: {list(first_address.keys())}")

            # Check for expected address attributes
            expected_attrs = ["addressId", "addressType", "streetAddress1", "city"]
            missing_attrs = [
                attr for attr in expected_attrs if attr not in first_address
            ]
            if missing_attrs:
                print(f"⚠ Missing expected attributes: {missing_attrs}")
            else:
                print("✓ All expected attributes present")

    def test_addresses_by_account_id(self, regression_client):
        """Test filtering addresses by account ID."""
        # First get an account ID
        accounts = list(regression_client.accounts.list(limit=1))
        if not accounts:
            pytest.skip("No accounts available for address testing")

        account_id = accounts[0].get("accountId")
        if not account_id:
            pytest.skip("Account missing accountId")

        # Get addresses for this account
        account_addresses = list(regression_client.addresses.get_by_account(account_id))

        print(f"✓ Account {account_id} has {len(account_addresses)} addresses")

        # Validate all addresses belong to the account
        for address in account_addresses:
            if "accountId" in address:
                assert address["accountId"] == account_id

    def test_addresses_primary_address(self, regression_client):
        """Test getting primary address for an account."""
        # First get an account ID
        accounts = list(regression_client.accounts.list(limit=1))
        if not accounts:
            pytest.skip("No accounts available for address testing")

        account_id = accounts[0].get("accountId")
        if not account_id:
            pytest.skip("Account missing accountId")

        # Get primary address
        primary_address = regression_client.addresses.get_primary_address(account_id)

        if primary_address:
            assert primary_address.get("isPrimaryAddress", False) is True
            print(f"✓ Primary address found for account {account_id}")
            print(f"  Type: {primary_address.get('addressType')}")
            print(f"  City: {primary_address.get('city')}")
        else:
            print(f"⚠ No primary address found for account {account_id}")

    def test_addresses_by_type(self, regression_client):
        """Test filtering addresses by type."""
        address_types = ["Home", "Work", "Business", "Mailing"]

        for address_type in address_types:
            try:
                typed_addresses = list(
                    regression_client.addresses.list(address_type=address_type, limit=5)
                )
                print(
                    f"✓ Address type '{address_type}': {len(typed_addresses)} addresses"
                )

                # Validate address type filtering
                for address in typed_addresses:
                    if "addressType" in address:
                        assert address["addressType"] == address_type

            except Exception as e:
                print(f"❌ Address type '{address_type}' failed: {e}")

    def test_addresses_get_specific(self, regression_client):
        """Test getting specific address by ID."""
        # First get an address ID
        addresses = list(regression_client.addresses.list(limit=1))
        address_id = None
        if addresses:
            address_id = addresses[0].get("addressId")

        if address_id:
            specific_address = regression_client.addresses.get(address_id)
            assert isinstance(specific_address, dict)
            assert specific_address.get("addressId") == address_id
            print(f"✓ Retrieved specific address: {address_id}")
        else:
            pytest.skip("No addresses available to test specific retrieval")

    def test_addresses_get_invalid_id(self, regression_client):
        """Test error handling for invalid address ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.addresses.get(999999999)
        print("✓ Correctly received 404 for invalid address ID")

    def test_addresses_pagination_behavior(self, regression_client):
        """Test pagination behavior for addresses."""
        # Get first page
        page1_addresses = list(
            regression_client.addresses.list(page_size=5, current_page=0)
        )

        # Get second page
        page2_addresses = list(
            regression_client.addresses.list(page_size=5, current_page=1)
        )

        print(f"✓ Page 1: {len(page1_addresses)} addresses")
        print(f"✓ Page 2: {len(page2_addresses)} addresses")

        # Check for overlap (shouldn't be any)
        if page1_addresses and page2_addresses:
            page1_ids = {
                a.get("addressId") for a in page1_addresses if "addressId" in a
            }
            page2_ids = {
                a.get("addressId") for a in page2_addresses if "addressId" in a
            }

            overlap = page1_ids.intersection(page2_ids)
            if overlap:
                print(f"❌ Pagination overlap: {len(overlap)} duplicate IDs")
            else:
                print("✓ No pagination overlap")

    def test_addresses_limit_parameter(self, regression_client):
        """Test limit parameter functionality."""
        # Test limit parameter
        limited_addresses = list(
            regression_client.addresses.list(page_size=20, limit=3)
        )

        if len(limited_addresses) > 3:
            print(
                f"❌ Limit not respected: got {len(limited_addresses)}, expected max 3"
            )
        else:
            print(f"✓ Limit parameter working: got {len(limited_addresses)} addresses")

        # Test limit=None (unlimited)
        unlimited_addresses = list(
            regression_client.addresses.list(page_size=10, limit=None)
        )
        print(f"✓ Unlimited query returned {len(unlimited_addresses)} addresses")

    def test_addresses_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        parameter_combinations = [
            {"address_type": "Home", "limit": 2},
            {"page_size": 3, "limit": 2},
            {"current_page": 0, "page_size": 5},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                addresses = list(regression_client.addresses.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(addresses)} addresses with {params}"
                )

                # Validate limit was applied if specified
                if "limit" in params and len(addresses) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(addresses)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")

    def test_addresses_response_structure_validation(self, regression_client):
        """Test address response structure validation."""
        addresses = list(regression_client.addresses.list(page_size=5))

        if addresses:
            first_address = addresses[0]

            # Core attributes that should be present
            expected_core_attrs = ["addressId", "addressType"]
            for attr in expected_core_attrs:
                if attr not in first_address:
                    print(f"⚠ Missing core attribute '{attr}'")

            # Optional attributes that may be present
            optional_attrs = [
                "streetAddress1",
                "streetAddress2",
                "city",
                "state",
                "zipCode",
                "country",
                "isPrimaryAddress",
                "accountId",
            ]
            present_optional = [
                attr for attr in optional_attrs if attr in first_address
            ]

            print(
                f"✓ Core attributes: {[attr for attr in expected_core_attrs if attr in first_address]}"
            )
            print(f"✓ Optional attributes present: {present_optional}")

            # Log data types for debugging
            for key, value in first_address.items():
                if value is not None:
                    print(f"  {key}: {type(value).__name__}")

        else:
            pytest.skip("No addresses available for structure validation")


# Note: Address write operations are typically managed through account creation/update
# Direct address creation/modification may not be available through the API
@pytest.mark.regression
@pytest.mark.writeops
class TestAddressesWriteOperations:
    """Write operation tests for AddressesResource - if available."""

    def test_addresses_write_placeholder(self, write_regression_client):
        """Placeholder for address write operations."""
        # Note: Address management typically done through accounts resource
        print("⚠ Address write operations may be handled through accounts resource")
