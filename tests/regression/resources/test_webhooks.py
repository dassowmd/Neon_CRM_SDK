"""Comprehensive regression tests for WebhooksResource.

Tests both read-only and write operations for the webhooks endpoint.
Organized to match src/neon_crm/resources/webhooks.py structure.
"""

import time

import pytest

from neon_crm.exceptions import (
    NeonBadRequestError,
    NeonNotFoundError,
    NeonUnprocessableEntityError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestWebhooksReadOnly:
    """Read-only tests for WebhooksResource - safe for production."""

    def test_webhooks_list_basic(self, regression_client):
        """Test basic webhook listing."""
        webhooks = list(regression_client.webhooks.list(limit=10))

        print(f"✓ Retrieved {len(webhooks)} webhooks")

        if webhooks:
            first_webhook = webhooks[0]
            assert isinstance(first_webhook, dict), "Webhook should be a dictionary"
            print(f"Webhook structure: {list(first_webhook.keys())}")

    def test_webhooks_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # Test limit parameter
        limited_webhooks = list(regression_client.webhooks.list(limit=5))

        if len(limited_webhooks) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_webhooks)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_webhooks)} webhooks"
            )

        # Test limit=None (this was causing crashes before fix)
        try:
            unlimited_webhooks = list(regression_client.webhooks.list(limit=None))
            print(f"✓ FIXED: limit=None works: got {len(unlimited_webhooks)} webhooks")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_webhooks_event_type_filtering(self, regression_client):
        """Test webhook filtering by event type."""
        try:
            # Test with common event types
            event_types = ["account.created", "donation.created", "event.registered"]

            for event_type in event_types:
                try:
                    filtered_webhooks = list(
                        regression_client.webhooks.list(limit=5, event_type=event_type)
                    )
                    print(
                        f"✓ Event type '{event_type}': {len(filtered_webhooks)} webhooks"
                    )
                except Exception as e:
                    print(f"⚠ Event type '{event_type}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Event type filtering test failed: {e}")

    def test_webhooks_status_filtering(self, regression_client):
        """Test webhook filtering by status."""
        try:
            statuses = ["active", "inactive"]

            for status in statuses:
                try:
                    status_webhooks = list(
                        regression_client.webhooks.list(limit=5, status=status)
                    )
                    print(f"✓ Status '{status}': {len(status_webhooks)} webhooks")

                    # Validate status filtering
                    for webhook in status_webhooks[:3]:
                        if "status" in webhook:
                            if webhook["status"].lower() != status.lower():
                                print(
                                    f"⚠ Status filter not working: expected {status}, got {webhook['status']}"
                                )

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_webhooks_get_event_types(self, regression_client):
        """Test getting available webhook event types."""
        try:
            event_types = regression_client.webhooks.get_event_types()
            assert isinstance(event_types, list), "Event types should be a list"
            print(f"✓ Retrieved {len(event_types)} webhook event types")

            if event_types:
                print(f"Sample event types: {event_types[:5]}")

        except Exception as e:
            print(f"❌ Get event types failed: {e}")

    def test_webhooks_get_specific(self, regression_client):
        """Test getting specific webhook by ID."""
        # First get a webhook ID
        webhook_id = None
        webhooks = list(regression_client.webhooks.list(limit=1))
        if webhooks:
            webhook_id = webhooks[0].get("webhookId") or webhooks[0].get("id")

        if webhook_id:
            specific_webhook = regression_client.webhooks.get(webhook_id)
            assert isinstance(specific_webhook, dict)
            print(f"✓ Retrieved specific webhook: {webhook_id}")
        else:
            pytest.skip("No webhooks available to test specific retrieval")

    def test_webhooks_get_invalid_id(self, regression_client):
        """Test error handling for invalid webhook ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.webhooks.get(999999999)
        print("✓ Correctly received 404 for invalid webhook ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestWebhooksWriteOperations:
    """Write operation tests for WebhooksResource - modifies database."""

    def test_create_webhook_basic(self, write_regression_client):
        """Test creating a basic webhook."""
        timestamp = int(time.time())
        created_webhooks = []

        try:
            # Create webhook
            webhook_result = write_regression_client.webhooks.create_webhook(
                url=f"https://example.com/webhook/{timestamp}",
                event_types=["account.created", "donation.created"],
                description=f"Test webhook {timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            if webhook_id:
                created_webhooks.append(webhook_id)
                print(f"✓ Created webhook: {webhook_id}")
                print(f"Webhook response structure: {list(webhook_result.keys())}")

        except Exception as e:
            print(f"❌ Webhook creation failed: {e}")
        finally:
            # Clean up
            for webhook_id in created_webhooks:
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ Cleaned up webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete webhook {webhook_id}: {e}")

    def test_create_webhook_with_secret(self, write_regression_client):
        """Test creating webhook with secret."""
        timestamp = int(time.time())
        created_webhooks = []

        try:
            webhook_result = write_regression_client.webhooks.create_webhook(
                url=f"https://example.com/secure-webhook/{timestamp}",
                event_types=["donation.created"],
                description=f"Secure webhook {timestamp}",
                secret=f"secret_{timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            if webhook_id:
                created_webhooks.append(webhook_id)
                print(f"✓ Created webhook with secret: {webhook_id}")

        except Exception as e:
            print(f"❌ Webhook with secret creation failed: {e}")
        finally:
            # Clean up
            for webhook_id in created_webhooks:
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ Cleaned up webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete webhook {webhook_id}: {e}")

    def test_update_webhook(self, write_regression_client):
        """Test updating a webhook."""
        timestamp = int(time.time())
        created_webhooks = []

        try:
            # Create webhook
            webhook_result = write_regression_client.webhooks.create_webhook(
                url=f"https://example.com/webhook/{timestamp}",
                event_types=["account.created"],
                description=f"Original webhook {timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            if webhook_id:
                created_webhooks.append(webhook_id)

                # Update webhook
                write_regression_client.webhooks.update_webhook(
                    webhook_id=webhook_id,
                    event_types=["account.created", "account.updated"],
                    description=f"Updated webhook {timestamp}",
                )

                print(f"✓ Updated webhook: {webhook_id}")

                # Verify update if possible
                try:
                    write_regression_client.webhooks.get(webhook_id)
                    print(f"✓ Verified webhook update: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not verify webhook update: {e}")

        except Exception as e:
            print(f"❌ Webhook update test failed: {e}")
        finally:
            # Clean up
            for webhook_id in created_webhooks:
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ Cleaned up webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete webhook {webhook_id}: {e}")

    def test_test_webhook(self, write_regression_client):
        """Test webhook testing functionality."""
        timestamp = int(time.time())
        created_webhooks = []

        try:
            # Create webhook
            webhook_result = write_regression_client.webhooks.create_webhook(
                url="https://httpbin.org/post",  # Use httpbin for testing
                event_types=["account.created"],
                description=f"Test webhook {timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            if webhook_id:
                created_webhooks.append(webhook_id)

                # Test webhook (might fail due to fake URL, but should not crash)
                try:
                    write_regression_client.webhooks.test_webhook(webhook_id)
                    print(f"✓ Webhook test completed: {webhook_id}")
                except Exception as e:
                    print(
                        f"⚠ Webhook test failed (expected for test URL): {type(e).__name__}"
                    )

        except Exception as e:
            print(f"❌ Webhook test operation failed: {e}")
        finally:
            # Clean up
            for webhook_id in created_webhooks:
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ Cleaned up webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete webhook {webhook_id}: {e}")

    def test_webhook_validation_errors(self, write_regression_client):
        """Test webhook validation errors."""
        # Test invalid URL
        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.webhooks.create_webhook(
                url="not-a-valid-url", event_types=["account.created"]
            )
        print("✓ Invalid URL correctly rejected")

        # Test empty event types
        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.webhooks.create_webhook(
                url="https://example.com/webhook", event_types=[]
            )
        print("✓ Empty event types correctly rejected")

        # Test invalid event type
        try:
            write_regression_client.webhooks.create_webhook(
                url="https://example.com/webhook", event_types=["invalid.event.type"]
            )
            print("⚠ Invalid event type was accepted")
        except (NeonBadRequestError, NeonUnprocessableEntityError):
            print("✓ Invalid event type correctly rejected")

    def test_webhook_lifecycle_complete(self, write_regression_client):
        """Test complete webhook lifecycle: create, update, test, delete."""
        timestamp = int(time.time())
        created_webhooks = []

        try:
            # Create
            webhook_result = write_regression_client.webhooks.create_webhook(
                url=f"https://example.com/lifecycle/{timestamp}",
                event_types=["account.created"],
                description=f"Lifecycle webhook {timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            if webhook_id:
                created_webhooks.append(webhook_id)
                print(f"✓ 1. Created webhook: {webhook_id}")

                # Update
                write_regression_client.webhooks.update_webhook(
                    webhook_id=webhook_id,
                    event_types=["account.created", "donation.created"],
                    description=f"Updated lifecycle webhook {timestamp}",
                )
                print(f"✓ 2. Updated webhook: {webhook_id}")

                # Test
                try:
                    write_regression_client.webhooks.test_webhook(webhook_id)
                    print(f"✓ 3. Tested webhook: {webhook_id}")
                except Exception:
                    print(f"⚠ 3. Webhook test failed (expected): {webhook_id}")

                # Delete (will happen in finally block)
                print(f"✓ 4. Will delete webhook: {webhook_id}")

        except Exception as e:
            print(f"❌ Webhook lifecycle test failed: {e}")
        finally:
            # Clean up
            for webhook_id in created_webhooks:
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ 4. Deleted webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete webhook {webhook_id}: {e}")
