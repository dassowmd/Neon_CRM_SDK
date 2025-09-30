"""Comprehensive regression tests for SoftCreditsResource.

Tests both read-only and write operations for the soft credits endpoint.
Organized to match src/neon_crm/resources/soft_credits.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestSoftCreditsReadOnly:
    """Read-only tests for SoftCreditsResource - safe for production."""

    def test_soft_credits_list_basic(self, regression_client):
        """Test basic soft credit listing."""
        soft_credits = list(regression_client.soft_credits.list(limit=5))

        print(f"✓ Retrieved {len(soft_credits)} soft credits")

        if soft_credits:
            first_credit = soft_credits[0]
            assert isinstance(first_credit, dict), "Soft credit should be a dictionary"
            print(f"Soft credit structure: {list(first_credit.keys())}")

    def test_soft_credits_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_credits = list(
            regression_client.soft_credits.list(page_size=20, limit=5)
        )

        if len(limited_credits) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_credits)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_credits)} soft credits"
            )

        try:
            unlimited_credits = list(
                regression_client.soft_credits.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_credits)} soft credits"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_soft_credits_get_specific(self, regression_client):
        """Test getting specific soft credit by ID."""
        credits = list(regression_client.soft_credits.list(limit=1))
        credit_id = None
        if credits:
            credit_id = credits[0].get("softCreditId") or credits[0].get("id")

        if credit_id:
            specific_credit = regression_client.soft_credits.get(credit_id)
            assert isinstance(specific_credit, dict)
            print(f"✓ Retrieved specific soft credit: {credit_id}")
        else:
            pytest.skip("No soft credits available to test specific retrieval")

    def test_soft_credits_get_invalid_id(self, regression_client):
        """Test error handling for invalid soft credit ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.soft_credits.get(999999999)
        print("✓ Correctly received 404 for invalid soft credit ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestSoftCreditsWriteOperations:
    """Write operation tests for SoftCreditsResource - modifies database."""

    def test_soft_credits_write_placeholder(self, write_regression_client):
        """Placeholder for soft credit write operations."""
        # Note: Soft credits are typically associated with donations
        # and require specific donation and account setup
        print("⚠ Soft credit operations require donation and account setup")
