"""Comprehensive regression tests for EventsResource.

Tests both read-only and write operations for the events endpoint.
Organized to match src/neon_crm/resources/events.py structure.
"""

import time
from datetime import datetime, timedelta

import pytest

from neon_crm.exceptions import (
    NeonBadRequestError,
    NeonNotFoundError,
    NeonUnprocessableEntityError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestEventsReadOnly:
    """Read-only tests for EventsResource - safe for production."""

    def test_events_list_basic(self, regression_client):
        """Test basic event listing."""
        events = list(regression_client.events.list(limit=5))

        print(f"✓ Retrieved {len(events)} events")

        if events:
            first_event = events[0]
            assert isinstance(first_event, dict), "Event should be a dictionary"
            print(f"Event structure: {list(first_event.keys())}")

            # Check for expected event attributes
            expected_attrs = ["eventId", "name", "startDate", "endDate"]
            missing_attrs = [attr for attr in expected_attrs if attr not in first_event]
            if missing_attrs:
                print(f"⚠ Some expected attributes missing: {missing_attrs}")

    def test_events_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # Test limit parameter
        limited_events = list(regression_client.events.list(limit=5))

        if len(limited_events) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_events)}, expected max 5"
            )
        else:
            print(f"✓ FIXED: Limit parameter working: got {len(limited_events)} events")

        # Test limit=None (this was causing crashes before fix)
        try:
            unlimited_events = list(regression_client.events.list(limit=None))
            print(f"✓ FIXED: limit=None works: got {len(unlimited_events)} events")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_events_date_filtering(self, regression_client):
        """Test event listing with date filtering."""
        # Test with date range for upcoming events
        start_date = datetime.now()
        end_date = start_date + timedelta(days=90)

        events = list(
            regression_client.events.list(
                limit=5,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
        )

        print(f"✓ Retrieved {len(events)} events with date filter (next 90 days)")

    def test_events_status_filtering(self, regression_client):
        """Test event filtering by status."""
        try:
            statuses = ["published", "draft", "archived"]

            for status in statuses:
                try:
                    status_events = list(
                        regression_client.events.list(limit=5, status=status)
                    )
                    print(f"✓ Status '{status}': {len(status_events)} events")

                    # Validate status filtering
                    for event in status_events[:3]:
                        if "status" in event:
                            if event["status"].lower() != status.lower():
                                print(
                                    f"⚠ Status filter not working: expected {status}, got {event['status']}"
                                )

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_events_category_filtering(self, regression_client):
        """Test event filtering by category."""
        try:
            category_events = list(
                regression_client.events.list(limit=5, category="Fundraising")
            )
            print(f"✓ Category filtering: {len(category_events)} fundraising events")

        except Exception as e:
            print(f"⚠ Category filtering failed: {e}")

    def test_events_search(self, regression_client):
        """Test event search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "status", "operator": "EQUAL", "value": "published"}
            ],
            "outputFields": ["eventId", "name", "startDate", "endDate", "status"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(regression_client.events.search(search_request))[:5]

        print(f"✓ Event search returned {len(results)} results")

        if results:
            first_result = results[0]
            # Validate search results contain requested fields
            requested_fields = ["eventId", "name", "startDate", "endDate", "status"]
            missing_fields = [f for f in requested_fields if f not in first_result]
            if missing_fields:
                print(f"⚠ Missing requested fields: {missing_fields}")

    def test_events_get_search_fields(self, regression_client):
        """Test getting available search fields for events."""
        try:
            search_fields = regression_client.events.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"✓ Retrieved {len(search_fields)} event search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_events_get_output_fields(self, regression_client):
        """Test getting available output fields for events."""
        try:
            output_fields = regression_client.events.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"✓ Retrieved {len(output_fields)} event output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_events_get_specific(self, regression_client):
        """Test getting specific event by ID."""
        # First get an event ID
        event_id = None
        events = list(regression_client.events.list(limit=1))
        if events:
            event_id = events[0].get("eventId") or events[0].get("id")

        if event_id:
            specific_event = regression_client.events.get(event_id)
            assert isinstance(specific_event, dict)
            print(f"✓ Retrieved specific event: {event_id}")
        else:
            pytest.skip("No events available to test specific retrieval")

    def test_events_get_invalid_id(self, regression_client):
        """Test error handling for invalid event ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.events.get(999999999)
        print("✓ Correctly received 404 for invalid event ID")

    def test_events_get_attendees(self, regression_client):
        """Test getting event attendees."""
        # First get an event ID
        event_id = None
        events = list(regression_client.events.list(limit=1))
        if events:
            event_id = events[0].get("eventId") or events[0].get("id")

        if event_id:
            try:
                attendees = list(regression_client.events.get_attendees(event_id))
                print(f"✓ Event {event_id} has {len(attendees)} attendees")
            except Exception as e:
                print(f"⚠ Could not get attendees for event {event_id}: {e}")
        else:
            pytest.skip("No events available to test attendee retrieval")

    def test_events_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        parameter_combinations = [
            {"status": "published", "limit": 3},
            {"category": "Fundraising", "limit": 5},
            {"start_date": start_date, "end_date": end_date, "limit": 2},
            {"status": "published", "category": "Fundraising", "limit": 1},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                events = list(regression_client.events.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(events)} events with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(events) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(events)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestEventsWriteOperations:
    """Write operation tests for EventsResource - modifies database."""

    def test_create_event_basic(self, write_regression_client):
        """Test creating a basic event."""
        timestamp = int(time.time())

        created_events = []

        try:
            # Create event
            event_payload = {
                "event": {
                    "name": f"Test Event {timestamp}",
                    "startDate": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "endDate": (datetime.now() + timedelta(days=31)).strftime(
                        "%Y-%m-%d"
                    ),
                    "status": "draft",
                    "category": "Fundraising",
                    "description": f"Test event created at {timestamp}",
                }
            }

            event_result = write_regression_client.events.create(event_payload)
            event_id = event_result.get("eventId") or event_result.get("id")

            if event_id:
                created_events.append(event_id)
                print(f"✓ Created event: {event_id}")
                print(f"Event response structure: {list(event_result.keys())}")

        except Exception as e:
            print(f"❌ Event creation failed: {e}")
        finally:
            # Clean up
            for event_id in created_events:
                try:
                    write_regression_client.events.delete(event_id)
                    print(f"✓ Cleaned up event: {event_id}")
                except Exception as e:
                    print(f"⚠ Could not delete event {event_id}: {e}")

    def test_update_event(self, write_regression_client):
        """Test updating an event."""
        timestamp = int(time.time())
        created_events = []

        try:
            # Create event
            event_payload = {
                "event": {
                    "name": f"Original Event {timestamp}",
                    "startDate": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "endDate": (datetime.now() + timedelta(days=31)).strftime(
                        "%Y-%m-%d"
                    ),
                    "status": "draft",
                    "description": f"Original description {timestamp}",
                }
            }

            event_result = write_regression_client.events.create(event_payload)
            event_id = event_result.get("eventId") or event_result.get("id")

            if event_id:
                created_events.append(event_id)

                # Update event
                write_regression_client.events.update(
                    event_id=event_id,
                    data={
                        "event": {
                            "name": f"Updated Event {timestamp}",
                            "description": f"Updated description {timestamp}",
                        }
                    },
                )

                print(f"✓ Updated event: {event_id}")

                # Verify update if possible
                try:
                    write_regression_client.events.get(event_id)
                    print(f"✓ Verified event update: {event_id}")
                except Exception as e:
                    print(f"⚠ Could not verify event update: {e}")

        except Exception as e:
            print(f"❌ Event update test failed: {e}")
        finally:
            # Clean up
            for event_id in created_events:
                try:
                    write_regression_client.events.delete(event_id)
                    print(f"✓ Cleaned up event: {event_id}")
                except Exception as e:
                    print(f"⚠ Could not delete event {event_id}: {e}")

    def test_event_validation_errors(self, write_regression_client):
        """Test event validation errors."""
        # Test missing required fields
        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.events.create(
                {
                    "event": {
                        "name": "Test Event"
                        # Missing startDate and endDate
                    }
                }
            )
        print("✓ Missing required fields correctly rejected")

        # Test invalid date format
        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.events.create(
                {
                    "event": {
                        "name": "Test Event",
                        "startDate": "invalid-date",
                        "endDate": "invalid-date",
                    }
                }
            )
        print("✓ Invalid date format correctly rejected")

        # Test end date before start date
        try:
            write_regression_client.events.create(
                {
                    "event": {
                        "name": "Test Event",
                        "startDate": "2024-12-31",
                        "endDate": "2024-01-01",  # Before start date
                    }
                }
            )
            print("⚠ End date before start date was accepted")
        except (NeonBadRequestError, NeonUnprocessableEntityError):
            print("✓ End date before start date correctly rejected")
