"""Accounts-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for accounts,
handling account-specific requirements like user_type parameters.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from ..types import UserType
from .base import BaseMigrationManager
from .bulk_migration import BulkMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class AccountsMigrationManager(BulkMigrationManager):
    """Migration manager specifically for accounts resource."""

    def __init__(
        self,
        accounts_resource,
        client: "NeonClient",
        user_type: Union[UserType, str] = UserType.INDIVIDUAL,
        **kwargs,
    ):
        """Initialize the accounts migration manager.

        Args:
            accounts_resource: The accounts resource instance
            client: Neon CRM client instance
            user_type: Default user type for account operations
            **kwargs: Additional parameters for account operations
        """
        super().__init__(accounts_resource, client, "accounts")
        self._user_type = user_type
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of accounts for conflict analysis.

        Args:
            resource_filter: Filter criteria for accounts
            limit: Maximum number of accounts to return

        Returns:
            List of account dictionaries
        """
        resources = []
        count = 0

        for resource in self.get_resources_for_migration(
            {"resource_filter": resource_filter}
        ):
            resources.append(resource)
            count += 1
            if count >= limit:
                break

        return resources

    def get_resources_for_migration(
        self, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Get accounts that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of account dictionaries
        """
        resource_filter = config.get("resource_filter")

        # Only fetch essential fields for migration - Account ID plus any source/target fields
        required_fields = ["Account ID"]
        if "required_fields" in config:
            required_fields.extend(config["required_fields"])

        # Prepare list parameters with required user_type
        list_params = {
            "user_type": self._user_type,
            "limit": 1000,
            **self._additional_params,
        }

        if resource_filter:
            # Use search with the provided filter
            search_request = {
                "searchFields": [
                    {"field": key, "operator": "EQUAL", "value": value}
                    for key, value in resource_filter.items()
                ],
                "outputFields": required_fields,
            }
            yield from self._resource.search(search_request)
        else:
            # Get all accounts with required user_type parameter and only required fields
            list_params["output_fields"] = required_fields
            yield from self._resource.list(**list_params)

    def get_resource_id_field(self) -> str:
        """Get the field name used for account IDs.

        Returns:
            Field name for account IDs
        """
        return "Account ID"

    def _find_resources_with_source_data(
        self,
        source_field: str,
        resource_filter: Optional[Dict[str, Any]] = None,
        required_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Find accounts that have data in the specified source field.

        This uses the built-in search_by_custom_field_value method that handles field name conversion.
        """
        self._logger.info(f"Searching for accounts with data in field '{source_field}'")

        # Use the existing search_by_custom_field_value method which handles custom field names properly
        accounts_with_data = []
        try:
            # Search for accounts where the field is NOT blank
            # We'll use a broad search approach - any account that has this field with any non-empty value

            # Unfortunately, search_by_custom_field_value doesn't support NOT_BLANK directly
            # Let's try common values that might exist: Yes, No, True, False, 1, 0, X, etc.
            common_values = ["Yes", "No", "True", "False", "1", "0", "X", "x", "Y", "y"]

            found_accounts = set()  # Use set to avoid duplicates

            for value in common_values:
                try:
                    # Use required_fields to limit the fields fetched for better performance
                    search_params = {"limit": 1000}
                    if required_fields:
                        search_params["output_fields"] = required_fields

                    for account in self._resource.search_by_custom_field_value(
                        source_field, value, **search_params
                    ):
                        account_id = account.get("Account ID")
                        if account_id and account_id not in found_accounts:
                            accounts_with_data.append(account)
                            found_accounts.add(account_id)

                        # Limit results for safety
                        if len(accounts_with_data) >= 5000:
                            break

                    if len(accounts_with_data) >= 5000:
                        break

                except Exception as e:
                    # Continue trying other values
                    self._logger.debug(f"Search for value '{value}' failed: {e}")
                    continue

            self._logger.info(
                f"Found {len(accounts_with_data)} accounts with data in '{source_field}' using value search"
            )

            # If we found accounts via value search, return them
            if accounts_with_data:
                return accounts_with_data

            # If no accounts found with common values, fall back to list approach
            self._logger.info(
                f"No accounts found with common values, falling back to list approach"
            )
            return self._fallback_find_resources_with_data(
                source_field, resource_filter, required_fields
            )

        except Exception as e:
            # Fallback to old approach if search fails
            self._logger.warning(f"Search failed for field '{source_field}': {e}")
            self._logger.info("Falling back to list approach")

            return self._fallback_find_resources_with_data(
                source_field, resource_filter, required_fields
            )

    def _fallback_find_resources_with_data(
        self,
        source_field: str,
        resource_filter: Optional[Dict[str, Any]] = None,
        required_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback method using list + filter approach."""
        accounts_with_data = []

        config = {"resource_filter": resource_filter}
        if required_fields:
            config["required_fields"] = required_fields
        for account in self.get_resources_for_migration(config):
            account_id = account.get("Account ID")
            if not account_id:
                continue

            # Check if this account has data in the source field
            source_value = self._value_manager.get_custom_field_value(
                account_id, source_field
            )
            if source_value is not None and str(source_value).strip():
                accounts_with_data.append(account)

                # Limit for safety
                if len(accounts_with_data) >= 1000:
                    break

        return accounts_with_data

    # Note: iterate_all_mappings method removed - it was impractical and slow
    # Real migrations should use specific field mappings via create_migration_plan_from_mapping()
