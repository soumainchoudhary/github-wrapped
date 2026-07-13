"""
Simple TTL in-memory cache backed by cachetools.
Keyed on (username, year) so the same user doesn't re-fetch within the TTL.
"""

from cachetools import TTLCache
from backend.app.core.config import settings

# One global cache instance shared across requests.
_cache: TTLCache = TTLCache(
    maxsize=settings.cache_max_size,
    ttl=settings.cache_ttl_seconds,
)


def get_cache() -> TTLCache:
    """Return the global TTL cache."""
    return _cache


def cache_key(username: str, year: int) -> str:
    """Build a consistent cache key."""
    return f"wrapped:{username.lower()}:{year}"
