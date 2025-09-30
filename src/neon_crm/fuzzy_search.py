"""Fuzzy search utilities for field names and other text matching."""

import re
from typing import Any, Dict, List, Tuple

try:
    import spacy

    # Load spaCy model at module level for efficiency
    nlp = spacy.load("en_core_web_md")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    nlp = None
    SPACY_AVAILABLE = False
    import warnings

    warnings.warn(
        "spaCy not available or English model not found. "
        "Install with: pip install spacy && python -m spacy download en_core_web_md. "
        "Falling back to rule-based semantic matching.",
        stacklevel=2,
    )

from .logging import NeonLogger


class SemanticMatcher:
    """Utility class for semantic similarity between field names."""

    def __init__(self):
        """Initialize the semantic matcher."""
        self._logger = NeonLogger.get_logger("semantic_search")

        # Common word transformations and abbreviations
        self.abbreviations = {
            "addr": "address",
            "st": "street",
            "ave": "avenue",
            "rd": "road",
            "dr": "drive",
            "ln": "lane",
            "blvd": "boulevard",
            "ct": "court",
            "apt": "apartment",
            "ste": "suite",
            "bldg": "building",
            "ph": "phone",
            "tel": "telephone",
            "mob": "mobile",
            "fax": "facsimile",
            "email": "electronic mail",
            "dob": "date of birth",
            "ssn": "social security number",
            "id": "identifier",
            "num": "number",
            "qty": "quantity",
            "amt": "amount",
            "org": "organization",
            "corp": "corporation",
            "co": "company",
            "dept": "department",
            "mgr": "manager",
            "rep": "representative",
            "info": "information",
            "desc": "description",
            "temp": "temporary",
            "pref": "preference",
            "req": "required",
            "opt": "optional",
            "vol": "volunteer",
            "mem": "member",
            "sub": "subscriber",
            "reg": "registration",
            "cert": "certificate",
            "qual": "qualification",
        }

        # Common synonyms and related terms
        self.synonyms = {
            "address": ["location", "residence", "home", "place", "site"],
            "phone": ["telephone", "mobile", "cell", "contact"],
            "email": ["mail", "electronic_mail", "contact"],
            "name": ["title", "label", "designation"],
            "first_name": ["given_name", "forename"],
            "last_name": ["surname", "family_name"],
            "company": ["organization", "business", "employer", "corporation"],
            "donation": ["gift", "contribution", "pledge"],
            "volunteer": ["service", "help", "assist"],
            "member": ["subscriber", "participant", "supporter"],
            "event": ["activity", "program", "meeting"],
            "date": ["time", "when", "timestamp"],
            "amount": ["value", "total", "sum", "cost", "price"],
            "type": ["kind", "category", "classification"],
            "status": ["state", "condition", "situation"],
        }

    def expand_abbreviations(self, text: str) -> List[str]:
        """Expand abbreviations in text to full forms.

        Args:
            text: Text that may contain abbreviations

        Returns:
            List of possible expansions
        """
        words = text.lower().replace("_", " ").replace("-", " ").split()
        expansions = [text.lower()]

        for word in words:
            if word in self.abbreviations:
                # Replace the abbreviation with full form
                expanded = text.lower().replace(word, self.abbreviations[word])
                expansions.append(expanded)

        return list(set(expansions))

    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word.

        Args:
            word: Word to find synonyms for

        Returns:
            List of synonyms
        """
        word = word.lower()
        synonyms = []

        # Direct lookup
        if word in self.synonyms:
            synonyms.extend(self.synonyms[word])

        # Reverse lookup (word might be a synonym of another word)
        for key, values in self.synonyms.items():
            if word in values:
                synonyms.append(key)
                synonyms.extend(values)

        return list(set(synonyms))

    def extract_meaningful_words(self, field_name: str) -> List[str]:
        """Extract meaningful words from a field name.

        Args:
            field_name: Field name to analyze

        Returns:
            List of meaningful words
        """
        # Handle camelCase, snake_case, and kebab-case
        import re

        # Split camelCase
        field_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", field_name)
        # Replace separators with spaces
        field_name = re.sub(r"[_\-\.]+", " ", field_name)

        # Split into words and filter out short/common words
        words = [word.lower().strip() for word in field_name.split() if word.strip()]

        # Filter out very short words and common words that don't add meaning
        stop_words = {
            "a",
            "an",
            "the",
            "of",
            "for",
            "in",
            "on",
            "at",
            "to",
            "is",
            "are",
            "and",
            "or",
        }
        meaningful_words = [
            word for word in words if len(word) > 2 and word not in stop_words
        ]

        return meaningful_words

    def calculate_semantic_similarity(self, field1: str, field2: str) -> float:
        """Calculate semantic similarity between two field names.

        Args:
            field1: First field name
            field2: Second field name

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if field1.lower() == field2.lower():
            return 1.0

        # Use spaCy for semantic similarity if available
        if SPACY_AVAILABLE and nlp:
            return self._calculate_spacy_similarity(field1, field2)

        # Fallback to rule-based similarity
        return self._calculate_rule_based_similarity(field1, field2)

    def _calculate_spacy_similarity(self, field1: str, field2: str) -> float:
        """Calculate semantic similarity using spaCy word vectors.

        Args:
            field1: First field name
            field2: Second field name

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Extract meaningful words from both fields
        words1 = self.extract_meaningful_words(field1)
        words2 = self.extract_meaningful_words(field2)

        if not words1 or not words2:
            return 0.0

        # Calculate semantic similarity between word pairs
        max_similarity = 0.0

        for word1 in words1:
            for word2 in words2:
                # Expand abbreviations first
                expanded1 = self.expand_abbreviations(word1)
                expanded2 = self.expand_abbreviations(word2)

                # Calculate similarity for all combinations
                for exp1 in expanded1:
                    for exp2 in expanded2:
                        try:
                            token1 = nlp(exp1)
                            token2 = nlp(exp2)

                            # spaCy similarity returns values between 0-1
                            similarity = token1.similarity(token2)
                            max_similarity = max(max_similarity, similarity)

                            # Early exit for very high similarity
                            if similarity > 0.9:
                                return similarity

                        except Exception as e:
                            # Log and continue if there's an error with spaCy
                            self._logger.debug(
                                f"spaCy similarity error for '{exp1}' and '{exp2}': {e}"
                            )
                            continue

        return max_similarity

    def _calculate_rule_based_similarity(self, field1: str, field2: str) -> float:
        """Fallback rule-based semantic similarity calculation.

        Args:
            field1: First field name
            field2: Second field name

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Extract meaningful words from both fields
        words1 = self.extract_meaningful_words(field1)
        words2 = self.extract_meaningful_words(field2)

        if not words1 or not words2:
            return 0.0

        # Expand words with abbreviations and synonyms
        expanded_words1 = set()
        expanded_words2 = set()

        for word in words1:
            expanded_words1.add(word)
            expanded_words1.update(self.expand_abbreviations(word))
            expanded_words1.update(self.get_synonyms(word))

        for word in words2:
            expanded_words2.add(word)
            expanded_words2.update(self.expand_abbreviations(word))
            expanded_words2.update(self.get_synonyms(word))

        # Calculate Jaccard similarity
        intersection = len(expanded_words1.intersection(expanded_words2))
        union = len(expanded_words1.union(expanded_words2))

        if union == 0:
            return 0.0

        return intersection / union

    def find_semantically_similar_fields(
        self,
        query: str,
        available_fields: List[str],
        threshold: float = 0.1,
        max_results: int = 10,
    ) -> List[Tuple[str, float]]:
        """Find semantically similar fields from a list of available fields.

        Args:
            query: Query field name or term
            available_fields: List of available field names to search through
            threshold: Minimum similarity score to include in results
            max_results: Maximum number of results to return

        Returns:
            List of (field_name, similarity_score) tuples sorted by score
        """
        if not query or not available_fields:
            return []

        self._logger.debug(
            f"Finding semantic matches for '{query}' in {len(available_fields)} fields"
        )

        matches = []
        for field in available_fields:
            score = self.calculate_semantic_similarity(query, field)
            if score >= threshold:
                matches.append((field, score))

        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        results = matches[:max_results]
        self._logger.debug(
            f"Found {len(results)} semantic matches above threshold {threshold}"
        )

        return results


class FuzzyMatcher:
    """Utility class for fuzzy string matching."""

    def __init__(self, case_sensitive: bool = False):
        """Initialize the fuzzy matcher.

        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
        self._logger = NeonLogger.get_logger("fuzzy_search")

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two strings.

        Uses a combination of different matching algorithms:
        - Exact match (highest score)
        - Starts with match
        - Contains match
        - Levenshtein distance
        - Word overlap

        Args:
            text1: First string to compare
            text2: Second string to compare

        Returns:
            Similarity score between 0.0 and 1.0 (1.0 = exact match)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize for comparison
        str1 = text1 if self.case_sensitive else text1.lower()
        str2 = text2 if self.case_sensitive else text2.lower()

        # Exact match
        if str1 == str2:
            return 1.0

        # Starts with match (high score)
        if str1.startswith(str2) or str2.startswith(str1):
            shorter = min(len(str1), len(str2))
            longer = max(len(str1), len(str2))
            return 0.9 * (shorter / longer)

        # Contains match
        if str2 in str1 or str1 in str2:
            shorter = min(len(str1), len(str2))
            longer = max(len(str1), len(str2))
            return 0.8 * (shorter / longer)

        # Word-based matching
        words1 = self._split_words(str1)
        words2 = self._split_words(str2)
        word_score = self._calculate_word_overlap(words1, words2)

        # Levenshtein distance
        distance_score = self._calculate_levenshtein_similarity(str1, str2)

        # Combine scores (word overlap weighted higher)
        return max(word_score * 0.7 + distance_score * 0.3, word_score, distance_score)

    def _split_words(self, text: str) -> List[str]:
        """Split text into words, handling various separators."""
        # Split on spaces, underscores, hyphens, and camelCase
        words = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # camelCase
        words = re.sub(r"[_\-\s]+", " ", words)  # separators
        return [word.strip() for word in words.split() if word.strip()]

    def _calculate_word_overlap(self, words1: List[str], words2: List[str]) -> float:
        """Calculate overlap score based on word matching."""
        if not words1 or not words2:
            return 0.0

        matches = 0
        total_words = max(len(words1), len(words2))

        for word1 in words1:
            for word2 in words2:
                if word1 == word2:
                    matches += 1
                    break
                elif word1.startswith(word2) or word2.startswith(word1):
                    matches += 0.8
                    break
                elif word2 in word1 or word1 in word2:
                    matches += 0.6
                    break

        return matches / total_words

    def _calculate_levenshtein_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity based on Levenshtein distance."""
        if len(str1) == 0:
            return 0.0 if len(str2) > 0 else 1.0
        if len(str2) == 0:
            return 0.0

        # Create matrix
        matrix = [[0] * (len(str2) + 1) for _ in range(len(str1) + 1)]

        # Initialize first row and column
        for i in range(len(str1) + 1):
            matrix[i][0] = i
        for j in range(len(str2) + 1):
            matrix[0][j] = j

        # Fill matrix
        for i in range(1, len(str1) + 1):
            for j in range(1, len(str2) + 1):
                if str1[i - 1] == str2[j - 1]:
                    cost = 0
                else:
                    cost = 1

                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,  # deletion
                    matrix[i][j - 1] + 1,  # insertion
                    matrix[i - 1][j - 1] + cost,  # substitution
                )

        distance = matrix[len(str1)][len(str2)]
        max_len = max(len(str1), len(str2))

        return 1.0 - (distance / max_len)

    def find_best_matches(
        self,
        query: str,
        candidates: List[str],
        threshold: float = 0.3,
        max_results: int = 10,
    ) -> List[Tuple[str, float]]:
        """Find the best matching candidates for a query.

        Args:
            query: The search query
            candidates: List of candidate strings to match against
            threshold: Minimum similarity score to include in results
            max_results: Maximum number of results to return

        Returns:
            List of (candidate, score) tuples sorted by score (highest first)
        """
        if not query or not candidates:
            return []

        self._logger.debug(
            f"Fuzzy matching '{query}' against {len(candidates)} candidates"
        )

        matches = []
        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score >= threshold:
                matches.append((candidate, score))

        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        results = matches[:max_results]
        self._logger.debug(f"Found {len(results)} matches above threshold {threshold}")

        return results


class FieldFuzzySearch:
    """Specialized fuzzy and semantic search for API fields."""

    def __init__(self, case_sensitive: bool = False):
        """Initialize the field fuzzy search.

        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.fuzzy_matcher = FuzzyMatcher(case_sensitive=case_sensitive)
        self.semantic_matcher = SemanticMatcher()
        self._logger = NeonLogger.get_logger("field_fuzzy_search")

    def search_custom_fields(
        self,
        query: str,
        custom_fields: List[Dict[str, Any]],
        threshold: float = 0.3,
        max_results: int = 10,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search custom fields by name with fuzzy matching.

        Args:
            query: The search query
            custom_fields: List of custom field dictionaries
            threshold: Minimum similarity score to include in results
            max_results: Maximum number of results to return

        Returns:
            List of (field_dict, score) tuples sorted by score
        """
        if not query or not custom_fields:
            return []

        self._logger.debug(
            f"Fuzzy searching {len(custom_fields)} custom fields for '{query}'"
        )

        matches = []
        for field in custom_fields:
            field_name = field.get("name", "")
            if field_name:
                score = self.fuzzy_matcher.calculate_similarity(query, field_name)
                if score >= threshold:
                    matches.append((field, score))

        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        results = matches[:max_results]
        self._logger.debug(f"Found {len(results)} custom field matches")

        return results

    def search_standard_fields(
        self,
        query: str,
        field_names: List[str],
        threshold: float = 0.3,
        max_results: int = 10,
    ) -> List[Tuple[str, float]]:
        """Search standard field names with fuzzy matching.

        Args:
            query: The search query
            field_names: List of standard field names
            threshold: Minimum similarity score to include in results
            max_results: Maximum number of results to return

        Returns:
            List of (field_name, score) tuples sorted by score
        """
        return self.fuzzy_matcher.find_best_matches(
            query, field_names, threshold, max_results
        )

    def suggest_corrections(
        self,
        invalid_field: str,
        available_fields: List[str],
        threshold: float = 0.4,
        max_suggestions: int = 5,
    ) -> List[str]:
        """Suggest field name corrections for invalid fields.

        Args:
            invalid_field: The invalid field name
            available_fields: List of valid field names
            threshold: Minimum similarity score for suggestions
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested field names
        """
        matches = self.fuzzy_matcher.find_best_matches(
            invalid_field, available_fields, threshold, max_suggestions
        )
        return [match[0] for match in matches]

    def search_fields_combined(
        self,
        query: str,
        available_fields: List[str],
        fuzzy_threshold: float = 0.3,
        semantic_threshold: float = 0.1,
        max_results: int = 10,
        combine_scores: bool = True,
    ) -> List[Tuple[str, float, str]]:
        """Search fields using both fuzzy and semantic matching.

        Args:
            query: The search query
            available_fields: List of available field names
            fuzzy_threshold: Minimum fuzzy similarity score
            semantic_threshold: Minimum semantic similarity score
            max_results: Maximum number of results to return
            combine_scores: Whether to combine fuzzy and semantic scores

        Returns:
            List of (field_name, score, match_type) tuples sorted by score
            match_type is 'fuzzy', 'semantic', or 'combined'
        """
        if not query or not available_fields:
            return []

        self._logger.debug(
            f"Combined search for '{query}' in {len(available_fields)} fields"
        )

        # Get fuzzy matches
        fuzzy_matches = self.fuzzy_matcher.find_best_matches(
            query, available_fields, fuzzy_threshold, max_results * 2
        )

        # Get semantic matches
        semantic_matches = self.semantic_matcher.find_semantically_similar_fields(
            query, available_fields, semantic_threshold, max_results * 2
        )

        # Combine and deduplicate results
        combined_results = {}

        # Add fuzzy matches
        for field, score in fuzzy_matches:
            combined_results[field] = {
                "fuzzy_score": score,
                "semantic_score": 0.0,
                "match_type": "fuzzy",
            }

        # Add semantic matches (and update existing entries)
        for field, score in semantic_matches:
            if field in combined_results:
                combined_results[field]["semantic_score"] = score
                combined_results[field]["match_type"] = "combined"
            else:
                combined_results[field] = {
                    "fuzzy_score": 0.0,
                    "semantic_score": score,
                    "match_type": "semantic",
                }

        # Calculate final scores and create result tuples
        final_results = []
        for field, scores in combined_results.items():
            if combine_scores:
                # Weighted combination: fuzzy 70%, semantic 30%
                final_score = (
                    scores["fuzzy_score"] * 0.7 + scores["semantic_score"] * 0.3
                )
            else:
                # Use the higher of the two scores
                final_score = max(scores["fuzzy_score"], scores["semantic_score"])

            final_results.append((field, final_score, scores["match_type"]))

        # Sort by score (highest first) and limit results
        final_results.sort(key=lambda x: x[1], reverse=True)
        results = final_results[:max_results]

        self._logger.debug(f"Found {len(results)} combined matches")
        return results

    def search_custom_fields_semantic(
        self,
        query: str,
        custom_fields: List[Dict[str, Any]],
        threshold: float = 0.1,
        max_results: int = 10,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search custom fields using semantic similarity.

        Args:
            query: The search query
            custom_fields: List of custom field dictionaries
            threshold: Minimum semantic similarity score
            max_results: Maximum number of results to return

        Returns:
            List of (field_dict, score) tuples sorted by score
        """
        if not query or not custom_fields:
            return []

        self._logger.debug(
            f"Semantic searching {len(custom_fields)} custom fields for '{query}'"
        )

        # Extract field names for semantic matching
        field_names = [
            field.get("name", "") for field in custom_fields if field.get("name")
        ]
        semantic_matches = self.semantic_matcher.find_semantically_similar_fields(
            query, field_names, threshold, max_results
        )

        # Map back to full field dictionaries
        name_to_field = {
            field.get("name", ""): field for field in custom_fields if field.get("name")
        }
        results = []
        for field_name, score in semantic_matches:
            if field_name in name_to_field:
                results.append((name_to_field[field_name], score))

        self._logger.debug(f"Found {len(results)} semantic custom field matches")
        return results
