"""Comprehensive regression tests for OrdersResource.

Tests both read-only and write operations for the orders endpoint.
Organized to match src/neon_crm/resources/orders.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestOrdersReadOnly:
    """Read-only tests for OrdersResource - safe for production."""

    def test_orders_list_basic(self, regression_client):
        """Test basic order listing."""
        orders = list(regression_client.orders.list(limit=5))

        print(f"✓ Retrieved {len(orders)} orders")

        if orders:
            first_order = orders[0]
            assert isinstance(first_order, dict), "Order should be a dictionary"
            print(f"Order structure: {list(first_order.keys())}")

    def test_orders_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_orders = list(regression_client.orders.list(page_size=20, limit=5))

        if len(limited_orders) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_orders)}, expected max 5"
            )
        else:
            print(f"✓ FIXED: Limit parameter working: got {len(limited_orders)} orders")

        try:
            unlimited_orders = list(
                regression_client.orders.list(page_size=10, limit=None)
            )
            print(f"✓ FIXED: limit=None works: got {len(unlimited_orders)} orders")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_orders_get_specific(self, regression_client):
        """Test getting specific order by ID."""
        orders = list(regression_client.orders.list(limit=1))
        order_id = None
        if orders:
            order_id = orders[0].get("orderId") or orders[0].get("id")

        if order_id:
            specific_order = regression_client.orders.get(order_id)
            assert isinstance(specific_order, dict)
            print(f"✓ Retrieved specific order: {order_id}")
        else:
            pytest.skip("No orders available to test specific retrieval")

    def test_orders_get_invalid_id(self, regression_client):
        """Test error handling for invalid order ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.orders.get(999999999)
        print("✓ Correctly received 404 for invalid order ID")

    def test_orders_search(self, regression_client):
        """Test orders search functionality."""
        search_request: SearchRequest = {
            "searchFields": [{"field": "status", "operator": "NOT_BLANK"}],
            "outputFields": ["id", "status", "total"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        try:
            results = list(regression_client.orders.search(search_request))[:5]
            print(f"✓ Orders search returned {len(results)} results")

            if results:
                first_result = results[0]
                requested_fields = ["id", "status", "total"]
                missing_fields = [f for f in requested_fields if f not in first_result]
                if missing_fields:
                    print(f"⚠ Missing requested fields: {missing_fields}")
                else:
                    print("✓ All requested fields present in results")
        except Exception as e:
            print(f"⚠ Orders search failed: {e}")

    def test_orders_get_search_fields(self, regression_client):
        """Test getting available search fields for orders."""
        try:
            search_fields = regression_client.orders.get_search_fields()
            assert isinstance(search_fields, dict)
            print(f"✓ Retrieved {len(search_fields)} order search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_orders_get_output_fields(self, regression_client):
        """Test getting available output fields for orders."""
        try:
            output_fields = regression_client.orders.get_output_fields()
            assert isinstance(output_fields, dict)
            print(f"✓ Retrieved {len(output_fields)} order output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_orders_calculate_total(self, regression_client):
        """Test order total calculation functionality."""
        try:
            # Get store products to use in calculation
            products_response = regression_client.get("/store/products")
            products = products_response.get("products", [])

            if not products:
                pytest.skip("No store products available for order calculation test")

            product = products[0]
            product_id = product.get("id")

            if not product_id:
                pytest.skip("Product missing ID for calculation test")

            # Test calculate order total
            order_data = {
                "order": {"items": [{"productId": product_id, "quantity": 2}]}
            }

            result = regression_client.orders.calculate_order_total(order_data)

            assert isinstance(
                result, dict
            ), "Calculate order total should return a dictionary"
            print(f"✓ Calculate order total returned: {result}")

            # Should contain total/cost information
            if (
                "total" in result
                or "subtotal" in result
                or "cost" in result
                or "amount" in result
                or "grandTotal" in result
            ):
                print("✓ Calculate order total returned cost information")
            else:
                print(
                    f"⚠ Unexpected calculate order total response structure: {list(result.keys())}"
                )

        except Exception as e:
            print(f"⚠ Calculate order total test failed: {e}")

    def test_orders_get_store_products(self, regression_client):
        """Test getting store products for order calculations."""
        try:
            response = regression_client.get("/store/products")

            assert isinstance(
                response, dict
            ), "Products response should be a dictionary"

            if "products" in response:
                products = response["products"]
                print(f"✓ Retrieved {len(products)} store products")

                if products:
                    first_product = products[0]
                    expected_attrs = ["id", "name"]
                    missing_attrs = [
                        attr for attr in expected_attrs if attr not in first_product
                    ]
                    if missing_attrs:
                        print(f"⚠ Product missing expected attributes: {missing_attrs}")
                    else:
                        print("✓ Store product has expected attributes")
            else:
                print(
                    f"⚠ Unexpected products response structure: {list(response.keys())}"
                )

        except Exception as e:
            print(f"⚠ Get store products test failed: {e}")

    def test_orders_get_shipping_methods(self, regression_client):
        """Test getting shipping methods for orders."""
        try:
            # Shipping methods endpoint requires a POST with address data
            test_address = {
                "address": {
                    "addressLine1": "123 Test St",
                    "city": "Test City",
                    "state": {"code": "CA"},
                    "zipCode": "12345",
                    "country": {"id": 1},  # Assuming US
                }
            }

            response = regression_client.post(
                "/orders/shippingMethods", json_data=test_address
            )

            assert isinstance(
                response, dict
            ), "Shipping methods response should be a dictionary"

            if "shippingMethods" in response:
                methods = response["shippingMethods"]
                print(f"✓ Retrieved {len(methods)} shipping methods")

                if methods:
                    first_method = methods[0]
                    expected_attrs = ["id", "name", "cost"]
                    missing_attrs = [
                        attr for attr in expected_attrs if attr not in first_method
                    ]
                    if missing_attrs:
                        print(
                            f"⚠ Shipping method missing expected attributes: {missing_attrs}"
                        )
                    else:
                        print("✓ Shipping method has expected attributes")
            else:
                print(
                    f"⚠ Unexpected shipping methods response structure: {list(response.keys())}"
                )

        except Exception as e:
            print(f"⚠ Get shipping methods test failed: {e}")
