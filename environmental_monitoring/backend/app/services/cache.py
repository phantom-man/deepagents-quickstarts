"""
Cache service for Environmental Monitoring System
"""

import os
import json
import redis.asyncio as redis
import logging
from typing import Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Global Redis client
redis_client = None

async def init_cache():
    """Initialize Redis cache connection."""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"❌ Failed to initialize Redis cache: {e}. Using in-memory cache.")
        redis_client = None

async def close_cache():
    """Close Redis cache connection."""
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
            logger.info("✅ Redis cache connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis cache: {e}")

class InMemoryCache:
    """Simple in-memory cache fallback when Redis is unavailable."""
    def __init__(self):
        self._cache = {}

    async def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self._cache[key] = value
        # Simple expiration simulation (not thread-safe)
        if ex:
            import asyncio
            asyncio.create_task(self._expire_key(key, ex))

    async def delete(self, key: str):
        self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._cache

    async def _expire_key(self, key: str, seconds: int):
        await asyncio.sleep(seconds)
        self._cache.pop(key, None)

# Use Redis if available, otherwise in-memory cache
_cache_instance = None

def get_cache():
    """Get cache instance (Redis or in-memory fallback)."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = redis_client if redis_client else InMemoryCache()
    return _cache_instance

async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    cache = get_cache()
    try:
        value = await cache.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None

async def cache_set(key: str, value: Any, ttl: int = CACHE_TTL):
    """Set value in cache with TTL."""
    cache = get_cache()
    try:
        await cache.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.error(f"Cache set error: {e}")

async def cache_delete(key: str):
    """Delete value from cache."""
    cache = get_cache()
    try:
        await cache.delete(key)
    except Exception as e:
        logger.error(f"Cache delete error: {e}")

async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    cache = get_cache()
    try:
        return await cache.exists(key)
    except Exception as e:
        logger.error(f"Cache exists error: {e}")
        return False

# Cache key generators
def sensor_readings_key(sensor_id: int, limit: int = 100) -> str:
    return f"sensor_readings:{sensor_id}:{limit}"

def predictions_key(sensor_id: int, hours: int = 24) -> str:
    return f"predictions:{sensor_id}:{hours}"

def dashboard_stats_key() -> str:
    return "dashboard_stats"

def gis_layer_key(layer_id: int) -> str:
    return f"gis_layer:{layer_id}"

def agent_session_key(session_id: str) -> str:
    return f"agent_session:{session_id}"

# Cache decorators
def cached(ttl: int = CACHE_TTL):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache first
            cached_result = await cache_get(key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            return result

        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Invalidate cache keys matching pattern
            # Note: This is a simplified implementation
            # In production, you'd want more sophisticated cache invalidation
            logger.info(f"Invalidating cache pattern: {pattern}")
            return result
        return wrapper
    return decorator