"""Tests for fuzzy search functionality."""

from unittest.mock import Mock, patch

import pytest

from neon_crm.fuzzy_search import FieldFuzzySearch, FuzzyMatcher, SemanticMatcher
from neon_crm.resources.custom_fields import FieldNotFoundError


class TestFuzzyMatcher:
    """Test the FuzzyMatcher class."""

    def test_exact_match(self):
        """Test exact string matching."""
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("test", "test")
        assert score == 1.0

    def test_case_sensitivity(self):
        """Test case sensitivity settings."""
        # Case insensitive
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("Test", "test")
        assert score == 1.0

        # Case sensitive
        matcher = FuzzyMatcher(case_sensitive=True)
        score = matcher.calculate_similarity("Test", "test")
        assert score < 1.0

    def test_starts_with_match(self):
        """Test starts with matching."""
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("volunteer", "vol")
        assert score > 0.2  # Should be decent score for starts-with

    def test_contains_match(self):
        """Test contains matching."""
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("volunteer_activities", "volunteer")
        assert score > 0.3  # Should be decent score for contains

    def test_word_overlap(self):
        """Test word-based matching."""
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("first_name", "firstName")
        assert score > 0.7  # Should match well despite different formatting

    def test_levenshtein_similarity(self):
        """Test Levenshtein distance calculation."""
        matcher = FuzzyMatcher(case_sensitive=False)
        score = matcher.calculate_similarity("volunteer", "volunter")  # missing 'e'
        assert score > 0.8  # Should be high similarity for one character difference

    def test_find_best_matches(self):
        """Test finding best matches from candidates."""
        matcher = FuzzyMatcher(case_sensitive=False)
        candidates = [
            "first_name",
            "last_name",
            "email_address",
            "phone_number",
            "volunteer_interests",
        ]

        matches = matcher.find_best_matches(
            "email", candidates, threshold=0.3, max_results=3
        )

        assert len(matches) <= 3
        assert all(score >= 0.3 for _, score in matches)
        # Results should be sorted by score (highest first)
        scores = [score for _, score in matches]
        assert scores == sorted(scores, reverse=True)

    def test_empty_inputs(self):
        """Test behavior with empty inputs."""
        matcher = FuzzyMatcher(case_sensitive=False)

        # Empty query
        assert matcher.calculate_similarity("", "test") == 0.0
        assert matcher.calculate_similarity("test", "") == 0.0
        assert matcher.calculate_similarity("", "") == 0.0

        # Empty candidates
        matches = matcher.find_best_matches("test", [], threshold=0.3)
        assert matches == []


class TestSemanticMatcher:
    """Test the SemanticMatcher class."""

    def test_expand_abbreviations(self):
        """Test abbreviation expansion."""
        matcher = SemanticMatcher()
        expansions = matcher.expand_abbreviations("ph_num")

        assert "ph_num" in expansions  # Original
        assert any("phone" in exp for exp in expansions)  # Should expand 'ph'

    def test_get_synonyms(self):
        """Test synonym retrieval."""
        matcher = SemanticMatcher()
        synonyms = matcher.get_synonyms("address")

        assert "location" in synonyms
        assert "residence" in synonyms
        assert len(synonyms) > 0

    def test_extract_meaningful_words(self):
        """Test meaningful word extraction."""
        matcher = SemanticMatcher()

        # Test camelCase
        words = matcher.extract_meaningful_words("firstName")
        assert "first" in words
        assert "name" in words

        # Test snake_case
        words = matcher.extract_meaningful_words("email_address")
        assert "email" in words
        assert "address" in words

        # Test kebab-case
        words = matcher.extract_meaningful_words("phone-number")
        assert "phone" in words
        assert "number" in words

    def test_calculate_semantic_similarity(self):
        """Test semantic similarity calculation."""
        matcher = SemanticMatcher()

        # Related terms should have high similarity
        score = matcher.calculate_semantic_similarity("address", "location")
        assert score > 0.3

        # Unrelated terms should have low similarity
        score = matcher.calculate_semantic_similarity("address", "volunteer")
        assert score < 0.5

    def test_find_semantically_similar_fields(self):
        """Test finding semantically similar fields."""
        matcher = SemanticMatcher()
        fields = [
            "home_address",
            "work_location",
            "volunteer_interests",
            "phone_number",
            "email_contact",
        ]

        matches = matcher.find_semantically_similar_fields(
            "address", fields, threshold=0.1, max_results=3
        )

        assert len(matches) <= 3
        # Should find address-related fields
        field_names = [field for field, _ in matches]
        assert any("address" in field or "location" in field for field in field_names)


class TestFieldFuzzySearch:
    """Test the FieldFuzzySearch class."""

    def test_search_custom_fields(self):
        """Test searching custom fields."""
        search = FieldFuzzySearch(case_sensitive=False)
        custom_fields = [
            {"name": "Volunteer Interests", "id": 123},
            {"name": "Email Preferences", "id": 124},
            {"name": "Home Address", "id": 125},
            {"name": "Work Location", "id": 126},
        ]

        results = search.search_custom_fields("volunteer", custom_fields, threshold=0.3)

        assert len(results) > 0
        field, score = results[0]
        assert field["name"] == "Volunteer Interests"
        assert score > 0.3  # Adjust threshold for realistic expectations

    def test_search_standard_fields(self):
        """Test searching standard field names."""
        search = FieldFuzzySearch(case_sensitive=False)
        field_names = ["first_name", "last_name", "email_address", "phone_number"]

        results = search.search_standard_fields("email", field_names, threshold=0.3)

        assert len(results) > 0
        field_name, score = results[0]
        assert "email" in field_name.lower()
        assert score > 0.3  # Adjust threshold for realistic expectations

    def test_suggest_corrections(self):
        """Test field name correction suggestions."""
        search = FieldFuzzySearch(case_sensitive=False)
        available_fields = [
            "first_name",
            "last_name",
            "email_address",
            "volunteer_interests",
        ]

        suggestions = search.suggest_corrections(
            "frist_name", available_fields, threshold=0.4
        )

        assert "first_name" in suggestions

    def test_search_fields_combined(self):
        """Test combined fuzzy and semantic search."""
        search = FieldFuzzySearch(case_sensitive=False)
        available_fields = [
            "home_address",
            "work_location",
            "volunteer_interests",
            "email_contact",
        ]

        results = search.search_fields_combined(
            "address", available_fields, fuzzy_threshold=0.3, semantic_threshold=0.1
        )

        assert len(results) > 0
        # Should find both fuzzy and semantic matches
        field_name, score, match_type = results[0]
        assert match_type in ["fuzzy", "semantic", "combined"]

    def test_search_custom_fields_semantic(self):
        """Test semantic search for custom fields."""
        search = FieldFuzzySearch(case_sensitive=False)
        custom_fields = [
            {"name": "Home Address", "id": 123},
            {"name": "Work Location", "id": 124},
            {"name": "Contact Phone", "id": 125},
        ]

        results = search.search_custom_fields_semantic(
            "address", custom_fields, threshold=0.1
        )

        assert len(results) > 0
        # Should find semantically related fields
        field_names = [field["name"] for field, _ in results]
        assert any("Address" in name or "Location" in name for name in field_names)


class TestFieldNotFoundError:
    """Test the FieldNotFoundError exception."""

    def test_error_message_with_suggestions(self):
        """Test error message formatting with suggestions."""
        fuzzy_suggestions = ["volunteer_interests", "volunteer_hours"]
        semantic_suggestions = ["member_activities", "service_history"]

        error = FieldNotFoundError(
            field_name="volunter",
            category="Account",
            fuzzy_suggestions=fuzzy_suggestions,
            semantic_suggestions=semantic_suggestions,
        )

        message = str(error)
        assert "volunter" in message
        assert "Account" in message
        assert "volunteer_interests" in message
        assert "member_activities" in message

    def test_error_message_no_suggestions(self):
        """Test error message when no suggestions found."""
        error = FieldNotFoundError(field_name="unknown_field", category="Account")

        message = str(error)
        assert "unknown_field" in message
        assert "No similar fields found" in message

    def test_error_attributes(self):
        """Test error attributes are properly set."""
        fuzzy_suggestions = ["field1", "field2"]
        semantic_suggestions = ["field3", "field4"]

        error = FieldNotFoundError(
            field_name="test_field",
            category="Donation",
            fuzzy_suggestions=fuzzy_suggestions,
            semantic_suggestions=semantic_suggestions,
        )

        assert error.field_name == "test_field"
        assert error.category == "Donation"
        assert error.fuzzy_suggestions == fuzzy_suggestions
        assert error.semantic_suggestions == semantic_suggestions


class TestIntegration:
    """Integration tests for fuzzy search functionality."""

    @patch("neon_crm.resources.custom_fields.CustomFieldsResource.get_by_category")
    def test_custom_fields_logging_suggestions(self, mock_get_by_category):
        """Test that custom field lookup logs suggestions when field not found."""
        from neon_crm.resources.custom_fields import CustomFieldsResource

        # Mock custom fields data
        mock_fields = [
            {"name": "Volunteer Interests", "id": 123},
            {"name": "Volunteer Hours", "id": 124},
            {"name": "Email Preferences", "id": 125},
        ]
        mock_get_by_category.return_value = mock_fields

        # Create resource with mock client and logger
        mock_client = Mock()
        mock_client._cache = None
        resource = CustomFieldsResource(mock_client)

        # Mock the logger to capture log messages
        with patch.object(resource._logger, "info") as mock_info:
            # Test field not found - should return None but log suggestions
            result = resource.find_by_name_and_category("volunter", "Account")

            assert result is None  # Original behavior - return None when not found
            mock_info.assert_called_once()  # Should have logged suggestions
            logged_message = mock_info.call_args[0][0]
            assert "volunter" in logged_message
            assert (
                "Did you mean" in logged_message
                or "Maybe you were looking for" in logged_message
            )

    @patch("neon_crm.resources.custom_fields.CustomFieldsResource.get_by_category")
    def test_custom_fields_find_exact_match(self, mock_get_by_category):
        """Test finding exact match for custom fields."""
        from neon_crm.resources.custom_fields import CustomFieldsResource

        # Mock custom fields data
        mock_fields = [
            {"name": "Volunteer Interests", "id": 123},
            {"name": "Email Preferences", "id": 124},
        ]
        mock_get_by_category.return_value = mock_fields

        # Create resource with mock client
        mock_client = Mock()
        mock_client._cache = None
        resource = CustomFieldsResource(mock_client)

        # Test exact field found
        result = resource.find_by_name_and_category("Volunteer Interests", "Account")

        assert result is not None
        assert result["name"] == "Volunteer Interests"
        assert result["id"] == 123

    def test_validation_logging_suggestions(self):
        """Test that field validation logs suggestions for invalid fields."""
        from neon_crm.validation import SearchRequestValidator

        # Create validator with mock client
        mock_client = Mock()
        validator = SearchRequestValidator("account", mock_client)

        # Mock both the field validation and available fields
        available_fields = [
            "first_name",
            "last_name",
            "email_address",
            "volunteer_interests",
        ]

        with patch.object(
            validator, "_is_valid_search_field", return_value=False
        ), patch.object(
            validator, "_get_available_search_fields", return_value=available_fields
        ), patch.object(validator._logger, "info") as mock_info:
            # Test invalid field - should log suggestions (using a closer match)
            search_field = {"field": "first_nam", "operator": "EQUAL", "value": "John"}
            errors = validator.validate_search_field(search_field)

            assert len(errors) > 0  # Should have validation errors
            mock_info.assert_called_once()  # Should have logged suggestions
            logged_message = mock_info.call_args[0][0]
            assert "first_nam" in logged_message
            assert "first_name" in logged_message

    def test_fuzzy_search_performance(self):
        """Test fuzzy search performance with larger datasets."""
        search = FieldFuzzySearch(case_sensitive=False)

        # Create larger dataset
        field_names = []
        for i in range(100):
            field_names.extend(
                [
                    f"field_{i}_name",
                    f"field_{i}_address",
                    f"field_{i}_email",
                    f"field_{i}_phone",
                    f"field_{i}_volunteer",
                ]
            )

        # Should handle large datasets efficiently
        import time

        start_time = time.time()
        results = search.search_standard_fields(
            "volunteer", field_names, threshold=0.3, max_results=10
        )
        end_time = time.time()

        # Should complete in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
        assert len(results) <= 10
        assert all("volunteer" in field.lower() for field, _ in results)

    def test_semantic_search_accuracy(self):
        """Test semantic search finds conceptually related terms."""
        search = FieldFuzzySearch(case_sensitive=False)

        # Fields with conceptually related but different names
        field_names = [
            "home_address",
            "work_location",
            "residence_info",
            "contact_phone",
            "mobile_number",
            "telephone",
            "email_address",
            "electronic_mail",
            "contact_email",
            "volunteer_service",
            "member_activities",
            "help_interests",
        ]

        # Test address-related search
        results = search.search_fields_combined(
            "address", field_names, semantic_threshold=0.1
        )
        address_fields = [
            field
            for field, _, _ in results
            if any(
                word in field.lower() for word in ["address", "location", "residence"]
            )
        ]
        assert len(address_fields) > 0

        # Test phone-related search
        results = search.search_fields_combined(
            "phone", field_names, semantic_threshold=0.1
        )
        phone_fields = [
            field
            for field, _, _ in results
            if any(word in field.lower() for word in ["phone", "mobile", "telephone"])
        ]
        assert len(phone_fields) > 0


if __name__ == "__main__":
    pytest.main([__file__])
