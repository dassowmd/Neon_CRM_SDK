"""Caching functionality for the Neon CRM SDK."""

import time
from threading import Lock
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from .logging import NeonLogger

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """A single cache entry with expiration."""

    def __init__(self, value: T, ttl_seconds: int = 300) -> None:
        """Initialize a cache entry.

        Args:
            value: The value to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds


class TTLCache(Generic[T]):
    """A thread-safe Time-To-Live cache implementation."""

    def __init__(self, default_ttl: int = 300) -> None:
        """Initialize the TTL cache.

        Args:
            default_ttl: Default time to live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self._logger = NeonLogger.get_logger("cache.ttl")

    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value if it exists and hasn't expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._logger.debug(f"Cache miss: {key}")
                return None

            if entry.is_expired():
                del self._cache[key]
                self._logger.debug(f"Cache expired: {key}")
                return None

            self._logger.debug(f"Cache hit: {key}")
            return entry.value

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (uses default if not provided)
        """
        ttl = ttl or self.default_ttl
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            self._logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> None:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> None:
        """Remove all expired entries from the cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._logger.debug(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )

    def size(self) -> int:
        """Get the number of entries in the cache."""
        with self._lock:
            return len(self._cache)

    def cache_get_or_set(
        self, key: str, fetch_func: Callable[[], T], ttl: Optional[int] = None
    ) -> T:
        """Get a value from cache or fetch and cache it if not present.

        Args:
            key: The cache key
            fetch_func: Function to call if cache miss
            ttl: Time to live in seconds (uses default if not provided)

        Returns:
            The cached or newly fetched value
        """
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        # Cache miss - fetch the value
        value = fetch_func()
        self.set(key, value, ttl)
        return value


class NeonCache:
    """Main cache manager for the Neon CRM SDK."""

    def __init__(self) -> None:
        """Initialize the Neon cache manager."""
        # Separate caches for different types of data
        self.custom_fields: TTLCache[Dict[str, Any]] = TTLCache(
            default_ttl=300
        )  # 5 minutes
        self.custom_field_groups: TTLCache[Dict[str, Any]] = TTLCache(default_ttl=300)
        self.custom_objects: TTLCache[Dict[str, Any]] = TTLCache(default_ttl=300)
        self.search_fields: TTLCache[Dict[str, Any]] = TTLCache(
            default_ttl=600
        )  # 10 minutes
        self.output_fields: TTLCache[Dict[str, Any]] = TTLCache(default_ttl=600)
        self._logger = NeonLogger.get_logger("cache.manager")

    def clear_all(self) -> None:
        """Clear all caches."""
        self.custom_fields.clear()
        self.custom_field_groups.clear()
        self.custom_objects.clear()
        self.search_fields.clear()
        self.output_fields.clear()
        self._logger.info("All caches cleared")

    def cleanup_expired(self) -> None:
        """Clean up expired entries from all caches."""
        self.custom_fields.cleanup_expired()
        self.custom_field_groups.cleanup_expired()
        self.custom_objects.cleanup_expired()
        self.search_fields.cleanup_expired()
        self.output_fields.cleanup_expired()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cache sizes.

        Returns:
            Dictionary with cache names and their sizes
        """
        return {
            "custom_fields": self.custom_fields.size(),
            "custom_field_groups": self.custom_field_groups.size(),
            "custom_objects": self.custom_objects.size(),
            "search_fields": self.search_fields.size(),
            "output_fields": self.output_fields.size(),
        }

    @classmethod
    def create_cache_key(cls, *parts: Any) -> str:
        """Create a cache key from multiple parts.

        Args:
            *parts: Parts to combine into a cache key

        Returns:
            A cache key string
        """
        # Convert all parts to strings and join with ":"
        return ":".join(str(part) for part in parts if part is not None)
