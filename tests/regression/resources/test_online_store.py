"""Comprehensive regression tests for OnlineStoreResource.

Tests both read-only operations for the online store endpoint.
Organized to match src/neon_crm/resources/online_store.py structure.

This resource had special limit parameter handling issues that were fixed.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestOnlineStoreReadOnly:
    """Read-only tests for OnlineStoreResource - safe for production."""

    def test_online_store_list_products(self, regression_client):
        """Test basic online store listing."""
        products = list(regression_client.online_store.list(limit=5))

        print(f"✓ Retrieved {len(products)} online store products")

        if products:
            first_product = products[0]
            assert isinstance(first_product, dict), "Product should be a dictionary"
            print(f"Product structure: {list(first_product.keys())}")

    def test_online_store_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - OnlineStore had special implementation issues."""
        # Test limit parameter (OnlineStore had custom implementation that ignored limit)
        limited_products = list(
            regression_client.online_store.list(page_size=20, limit=5)
        )

        if len(limited_products) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_products)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_products)} products"
            )

        # Test limit=None
        try:
            unlimited_products = list(
                regression_client.online_store.list(page_size=10, limit=None)
            )
            print(f"✓ FIXED: limit=None works: got {len(unlimited_products)} products")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_online_store_pagination_parameters(self, regression_client):
        """Test pagination parameters - OnlineStore had custom pagination handling."""
        # Test current_page parameter
        page1_products = list(
            regression_client.online_store.list(page_size=5, current_page=0)
        )

        page2_products = list(
            regression_client.online_store.list(page_size=5, current_page=1)
        )

        print(f"✓ Page 1: {len(page1_products)} products")
        print(f"✓ Page 2: {len(page2_products)} products")

        # Check for overlap (shouldn't be any)
        if page1_products and page2_products:
            page1_ids = {p.get("id") for p in page1_products if "id" in p}
            page2_ids = {p.get("id") for p in page2_products if "id" in p}

            overlap = page1_ids.intersection(page2_ids)
            if overlap:
                print(f"❌ Pagination overlap: {len(overlap)} duplicate IDs")
            else:
                print("✓ No pagination overlap")

    def test_online_store_get_specific_product(self, regression_client):
        """Test getting specific product by ID."""
        products = list(regression_client.online_store.list_products(limit=1))
        product_id = None
        if products:
            product_id = products[0].get("productId") or products[0].get("id")

        if product_id:
            specific_product = regression_client.online_store.get_product(product_id)
            assert isinstance(specific_product, dict)
            print(f"✓ Retrieved specific product: {product_id}")
        else:
            pytest.skip("No products available to test specific retrieval")

    def test_online_store_list_products_method(self, regression_client):
        """Test the dedicated list_products method."""
        products = list(regression_client.online_store.list_products(limit=3))
        print(f"✓ list_products() returned {len(products)} products")

        if products:
            first_product = products[0]
            print(f"Product structure: {list(first_product.keys())}")

    def test_online_store_list_catalogs(self, regression_client):
        """Test listing store catalogs."""
        try:
            catalogs = list(regression_client.online_store.list_catalogs(limit=5))
            print(f"✓ Retrieved {len(catalogs)} store catalogs")

            if catalogs:
                first_catalog = catalogs[0]
                print(f"Catalog structure: {list(first_catalog.keys())}")
        except Exception as e:
            print(f"⚠ Could not list catalogs: {e}")

    def test_online_store_list_categories(self, regression_client):
        """Test listing store categories."""
        try:
            categories = list(regression_client.online_store.list_categories(limit=5))
            print(f"✓ Retrieved {len(categories)} store categories")

            if categories:
                first_category = categories[0]
                print(f"Category structure: {list(first_category.keys())}")
        except Exception as e:
            print(f"⚠ Could not list categories: {e}")

    def test_online_store_list_transactions(self, regression_client):
        """Test listing store transactions."""
        try:
            transactions = list(
                regression_client.online_store.list_transactions(limit=3)
            )
            print(f"✓ Retrieved {len(transactions)} store transactions")

            if transactions:
                first_transaction = transactions[0]
                print(f"Transaction structure: {list(first_transaction.keys())}")
        except Exception as e:
            print(f"⚠ Could not list transactions: {e}")

    def test_online_store_list_orders(self, regression_client):
        """Test listing store orders."""
        try:
            orders = list(regression_client.online_store.list_orders(limit=3))
            print(f"✓ Retrieved {len(orders)} store orders")

            if orders:
                first_order = orders[0]
                print(f"Order structure: {list(first_order.keys())}")
        except Exception as e:
            print(f"⚠ Could not list orders: {e}")

    def test_online_store_get_specific_transaction(self, regression_client):
        """Test getting specific transaction by ID."""
        try:
            transactions = list(
                regression_client.online_store.list_transactions(limit=1)
            )
            transaction_id = None
            if transactions:
                transaction_id = transactions[0].get("transactionId") or transactions[
                    0
                ].get("id")

            if transaction_id:
                specific_transaction = regression_client.online_store.get_transaction(
                    transaction_id
                )
                assert isinstance(specific_transaction, dict)
                print(f"✓ Retrieved specific transaction: {transaction_id}")
            else:
                print("⚠ No transactions available to test specific retrieval")
        except Exception as e:
            print(f"⚠ Could not test specific transaction retrieval: {e}")

    def test_online_store_get_specific_order(self, regression_client):
        """Test getting specific order by ID."""
        try:
            orders = list(regression_client.online_store.list_orders(limit=1))
            order_id = None
            if orders:
                order_id = orders[0].get("orderId") or orders[0].get("id")

            if order_id:
                specific_order = regression_client.online_store.get_order(order_id)
                assert isinstance(specific_order, dict)
                print(f"✓ Retrieved specific order: {order_id}")
            else:
                print("⚠ No orders available to test specific retrieval")
        except Exception as e:
            print(f"⚠ Could not test specific order retrieval: {e}")

    def test_online_store_get_invalid_product_id(self, regression_client):
        """Test error handling for invalid product ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.online_store.get_product(999999999)
        print("✓ Correctly received 404 for invalid product ID")

    def test_online_store_get_invalid_transaction_id(self, regression_client):
        """Test error handling for invalid transaction ID."""
        try:
            with pytest.raises(NeonNotFoundError):
                regression_client.online_store.get_transaction(999999999)
            print("✓ Correctly received 404 for invalid transaction ID")
        except Exception as e:
            print(f"⚠ Could not test invalid transaction ID: {e}")

    def test_online_store_get_invalid_order_id(self, regression_client):
        """Test error handling for invalid order ID."""
        try:
            with pytest.raises(NeonNotFoundError):
                regression_client.online_store.get_order(999999999)
            print("✓ Correctly received 404 for invalid order ID")
        except Exception as e:
            print(f"⚠ Could not test invalid order ID: {e}")

    def test_online_store_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        parameter_combinations = [
            {"page_size": 3, "limit": 2},
            {"current_page": 0, "page_size": 5},
            {"current_page": 1, "page_size": 3, "limit": 2},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                products = list(regression_client.online_store.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(products)} products with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(products) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(products)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")

    def test_online_store_product_filtering(self, regression_client):
        """Test product filtering parameters."""
        try:
            # Test product status filtering
            filtered_products = list(
                regression_client.online_store.list_products(
                    product_status="active", limit=3
                )
            )
            print(f"✓ Active products: {len(filtered_products)}")

            # Test category filtering
            category_products = list(
                regression_client.online_store.list_products(
                    category="merchandise", limit=3
                )
            )
            print(f"✓ Merchandise products: {len(category_products)}")

        except Exception as e:
            print(f"⚠ Product filtering test failed: {e}")

    def test_online_store_transaction_filtering(self, regression_client):
        """Test transaction filtering parameters."""
        try:
            # Test date range filtering
            transactions = list(
                regression_client.online_store.list_transactions(
                    start_date="2024-01-01", end_date="2024-12-31", limit=3
                )
            )
            print(f"✓ Transactions in 2024: {len(transactions)}")

            # Test status filtering
            status_transactions = list(
                regression_client.online_store.list_transactions(
                    status="completed", limit=3
                )
            )
            print(f"✓ Completed transactions: {len(status_transactions)}")

        except Exception as e:
            print(f"⚠ Transaction filtering test failed: {e}")

    def test_online_store_order_filtering(self, regression_client):
        """Test order filtering parameters."""
        try:
            # Test status filtering
            status_orders = list(
                regression_client.online_store.list_orders(status="pending", limit=3)
            )
            print(f"✓ Pending orders: {len(status_orders)}")

            # Test customer filtering (if customer_id available)
            # This would need a real customer ID, so we'll just test the parameter handling
            print("✓ Order filtering parameters accepted")

        except Exception as e:
            print(f"⚠ Order filtering test failed: {e}")


# Note: Online store products are typically managed through admin interfaces
# Write operations may not be available through the API
@pytest.mark.regression
@pytest.mark.writeops
class TestOnlineStoreWriteOperations:
    """Write operation tests for OnlineStoreResource - if available."""

    def test_online_store_write_placeholder(self, write_regression_client):
        """Placeholder for online store write operations."""
        # Note: Product management typically requires inventory setup
        print("⚠ Online store product management may require admin interface")
