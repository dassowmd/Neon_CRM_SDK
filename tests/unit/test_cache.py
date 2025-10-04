"""Unit tests for the cache module."""

import time

from neon_crm.cache import CacheEntry, NeonCache, TTLCache


class TestCacheEntry:
    """Test the CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        value = {"test": "data"}
        entry = CacheEntry(value, ttl_seconds=60)

        assert entry.value == value
        assert entry.ttl_seconds == 60
        assert entry.created_at <= time.time()

    def test_cache_entry_default_ttl(self):
        """Test cache entry with default TTL."""
        entry = CacheEntry("test")
        assert entry.ttl_seconds == 300  # 5 minutes default

    def test_cache_entry_not_expired_when_new(self):
        """Test that new cache entry is not expired."""
        entry = CacheEntry("test", ttl_seconds=60)
        assert not entry.is_expired()

    def test_cache_entry_expired_after_ttl(self):
        """Test that cache entry expires after TTL."""
        entry = CacheEntry("test", ttl_seconds=0.1)  # 100ms
        time.sleep(0.2)  # Wait 200ms
        assert entry.is_expired()

    def test_cache_entry_not_expired_before_ttl(self):
        """Test that cache entry doesn't expire before TTL."""
        entry = CacheEntry("test", ttl_seconds=1)  # 1 second
        assert not entry.is_expired()


class TestTTLCache:
    """Test the TTLCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = TTLCache(default_ttl=120)
        assert cache.default_ttl == 120
        assert cache.size() == 0

    def test_cache_set_and_get(self):
        """Test basic set and get operations."""
        cache = TTLCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_cache_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        cache = TTLCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_set_with_custom_ttl(self):
        """Test setting with custom TTL."""
        cache = TTLCache(default_ttl=300)
        cache.set("key1", "value1", ttl=60)

        # Should still be available
        assert cache.get("key1") == "value1"

    def test_cache_expiration(self):
        """Test that entries expire after TTL."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl=0.1)  # 100ms

        # Should be available immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.2)

        # Should be None after expiration
        assert cache.get("key1") is None

    def test_cache_delete(self):
        """Test deleting a cache entry."""
        cache = TTLCache()
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_delete_nonexistent_key(self):
        """Test deleting a non-existent key doesn't raise error."""
        cache = TTLCache()
        cache.delete("nonexistent")  # Should not raise

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = TTLCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_size(self):
        """Test cache size tracking."""
        cache = TTLCache()
        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.delete("key1")
        assert cache.size() == 1

    def test_cache_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl=0.1)  # Will expire
        cache.set("key2", "value2", ttl=60)  # Won't expire

        assert cache.size() == 2

        # Wait for first entry to expire
        time.sleep(0.2)

        cache.cleanup_expired()
        assert cache.size() == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_get_or_set_hit(self):
        """Test cache_get_or_set with cache hit."""
        cache = TTLCache()
        cache.set("key1", "cached_value")

        def fetch_func():
            return "fetched_value"

        result = cache.cache_get_or_set("key1", fetch_func)
        assert result == "cached_value"  # Should return cached value

    def test_cache_get_or_set_miss(self):
        """Test cache_get_or_set with cache miss."""
        cache = TTLCache()

        def fetch_func():
            return "fetched_value"

        result = cache.cache_get_or_set("key1", fetch_func)
        assert result == "fetched_value"

        # Should now be cached
        assert cache.get("key1") == "fetched_value"

    def test_cache_get_or_set_with_custom_ttl(self):
        """Test cache_get_or_set with custom TTL."""
        cache = TTLCache()

        def fetch_func():
            return "fetched_value"

        result = cache.cache_get_or_set("key1", fetch_func, ttl=60)
        assert result == "fetched_value"
        assert cache.get("key1") == "fetched_value"

    def test_cache_thread_safety(self):
        """Test that cache operations are thread-safe."""
        import threading

        cache = TTLCache()
        results = []

        def cache_operation(i):
            cache.set(f"key{i}", f"value{i}")
            result = cache.get(f"key{i}")
            results.append(result)

        threads = [
            threading.Thread(target=cache_operation, args=(i,)) for i in range(10)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(results) == 10
        for i in range(10):
            assert f"value{i}" in results

    def test_cache_handles_complex_objects(self):
        """Test that cache can handle complex objects."""
        cache = TTLCache()
        complex_obj = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
        }

        cache.set("complex", complex_obj)
        result = cache.get("complex")

        assert result == complex_obj
        assert result is complex_obj  # Should be same object reference


class TestNeonCache:
    """Test the NeonCache class."""

    def test_neon_cache_initialization(self):
        """Test NeonCache initialization."""
        cache = NeonCache()

        assert isinstance(cache.custom_fields, TTLCache)
        assert isinstance(cache.custom_field_groups, TTLCache)
        assert isinstance(cache.custom_objects, TTLCache)
        assert isinstance(cache.search_fields, TTLCache)
        assert isinstance(cache.output_fields, TTLCache)

    def test_neon_cache_ttl_settings(self):
        """Test that different caches have appropriate TTL settings."""
        cache = NeonCache()

        # Custom fields should have 5 minute TTL
        assert cache.custom_fields.default_ttl == 300
        assert cache.custom_field_groups.default_ttl == 300
        assert cache.custom_objects.default_ttl == 300

        # Search/output fields should have 10 minute TTL
        assert cache.search_fields.default_ttl == 600
        assert cache.output_fields.default_ttl == 600

    def test_neon_cache_clear_all(self):
        """Test clearing all caches."""
        cache = NeonCache()

        # Add data to all caches
        cache.custom_fields.set("key1", "value1")
        cache.custom_field_groups.set("key2", "value2")
        cache.custom_objects.set("key3", "value3")
        cache.search_fields.set("key4", "value4")
        cache.output_fields.set("key5", "value5")

        # Verify data is there
        assert cache.custom_fields.size() == 1
        assert cache.custom_field_groups.size() == 1
        assert cache.custom_objects.size() == 1
        assert cache.search_fields.size() == 1
        assert cache.output_fields.size() == 1

        # Clear all
        cache.clear_all()

        # Verify all are empty
        assert cache.custom_fields.size() == 0
        assert cache.custom_field_groups.size() == 0
        assert cache.custom_objects.size() == 0
        assert cache.search_fields.size() == 0
        assert cache.output_fields.size() == 0

    def test_neon_cache_cleanup_expired(self):
        """Test cleaning up expired entries from all caches."""
        cache = NeonCache()

        # Add entries with short TTL
        cache.custom_fields.set("key1", "value1", ttl=0.1)
        cache.search_fields.set("key2", "value2", ttl=60)  # Won't expire

        assert cache.custom_fields.size() == 1
        assert cache.search_fields.size() == 1

        # Wait for expiration
        time.sleep(0.2)

        cache.cleanup_expired()

        # Only the non-expired entry should remain
        assert cache.custom_fields.size() == 0
        assert cache.search_fields.size() == 1

    def test_neon_cache_get_cache_stats(self):
        """Test getting cache statistics."""
        cache = NeonCache()

        stats = cache.get_cache_stats()
        expected_keys = {
            "custom_fields",
            "custom_field_groups",
            "custom_objects",
            "search_fields",
            "output_fields",
        }

        assert set(stats.keys()) == expected_keys
        assert all(isinstance(size, int) for size in stats.values())

        # All should be 0 initially
        assert all(size == 0 for size in stats.values())

        # Add some data
        cache.custom_fields.set("key1", "value1")
        cache.search_fields.set("key2", "value2")

        stats = cache.get_cache_stats()
        assert stats["custom_fields"] == 1
        assert stats["search_fields"] == 1
        assert stats["custom_field_groups"] == 0

    def test_create_cache_key(self):
        """Test cache key creation."""
        key1 = NeonCache.create_cache_key("part1", "part2", "part3")
        assert key1 == "part1:part2:part3"

        key2 = NeonCache.create_cache_key("single")
        assert key2 == "single"

        key3 = NeonCache.create_cache_key(123, "text", 456)
        assert key3 == "123:text:456"

    def test_create_cache_key_with_none_values(self):
        """Test cache key creation with None values."""
        key = NeonCache.create_cache_key("part1", None, "part3", None)
        assert key == "part1:part3"

    def test_create_cache_key_empty(self):
        """Test cache key creation with no parts."""
        key = NeonCache.create_cache_key()
        assert key == ""

    def test_cache_integration_example(self):
        """Test a realistic integration example."""
        cache = NeonCache()

        # Simulate custom field lookup
        field_key = cache.create_cache_key(
            "custom_field", "ACCOUNT", "Email Preference"
        )

        def fetch_field():
            return {"id": 123, "name": "Email Preference", "type": "text"}

        # First call should fetch and cache
        result1 = cache.custom_fields.cache_get_or_set(field_key, fetch_field)
        assert result1["id"] == 123

        # Second call should hit cache
        result2 = cache.custom_fields.cache_get_or_set(
            field_key, lambda: {"should": "not_be_called"}
        )
        assert result2["id"] == 123  # Same as cached result
