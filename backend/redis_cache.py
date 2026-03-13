#!/usr/bin/env python3
"""
Redis caching module for the Reach application.
Provides caching for the public sender page with graceful fallback.
"""

import os
import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timezone
import asyncio

# Try to import redis, but handle missing dependency gracefully
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logging.warning("Redis not installed. Install with: pip install redis")

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis caching client with graceful fallback."""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self._init_attempted = False
        
    async def initialize(self):
        """Initialize Redis connection if available."""
        if self._init_attempted:
            return
            
        self._init_attempted = True
        
        if not REDIS_AVAILABLE:
            logger.info("Redis library not available, caching disabled")
            return
            
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url or redis_url == "redis://default:password@redis-host:6379":
            logger.info("REDIS_URL not configured or using placeholder, caching disabled")
            return
            
        try:
            # Parse Redis URL
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,  # Automatically decode responses to strings
                socket_connect_timeout=5,  # 5 second connection timeout
                socket_keepalive=True,
                retry_on_timeout=True,
                max_connections=10
            )
            
            # Test connection
            await self.client.ping()
            self.connected = True
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            self.connected = False
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            # Ensure client is None if connection failed
            self.client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or Redis unavailable
        """
        if not self.connected or not self.client:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # If not JSON, return as string
                    return value
            return None
        except Exception as e:
            logger.debug(f"Redis get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected or not self.client:
            return False
            
        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list, tuple, int, float, bool, type(None))):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
                
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Redis set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected or not self.client:
            return False
            
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.debug(f"Redis delete failed for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "reach:public:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.connected or not self.client:
            return 0
            
        try:
            # Use SCAN to find all keys matching pattern
            keys = []
            cursor = 0
            while True:
                cursor, found_keys = await self.client.scan(cursor=cursor, match=pattern, count=100)
                keys.extend(found_keys)
                if cursor == 0:
                    break
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.debug(f"Redis delete_pattern failed for pattern {pattern}: {e}")
            return 0
    
    async def invalidate_public_reach_page(self, handle: str) -> bool:
        """
        Invalidate cache for a specific public reach page.
        
        Args:
            handle: Identity handle
            
        Returns:
            True if successful, False otherwise
        """
        key = f"reach:public:{handle.lower()}"
        return await self.delete(key)
    
    async def invalidate_all_public_reach_pages(self) -> int:
        """
        Invalidate all public reach page caches.
        
        Returns:
            Number of keys deleted
        """
        return await self.delete_pattern("reach:public:*")
    
    async def get_public_reach_page(self, handle: str) -> Optional[Dict[str, Any]]:
        """
        Get cached public reach page data.
        
        Args:
            handle: Identity handle
            
        Returns:
            Cached data or None if not found
        """
        key = f"reach:public:{handle.lower()}"
        return await self.get(key)
    
    async def set_public_reach_page(self, handle: str, data: Dict[str, Any]) -> bool:
        """
        Cache public reach page data.
        
        Args:
            handle: Identity handle
            data: Page data to cache
            
        Returns:
            True if successful, False otherwise
        """
        key = f"reach:public:{handle.lower()}"
        # Cache for 5 minutes (300 seconds)
        return await self.set(key, data, ttl=300)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health status.
        
        Returns:
            Dictionary with health information
        """
        status = {
            "redis_available": REDIS_AVAILABLE,
            "connected": self.connected,
            "client_initialized": self.client is not None,
            "init_attempted": self._init_attempted,
        }
        
        if self.connected and self.client:
            try:
                await self.client.ping()
                status["ping"] = "ok"
            except Exception as e:
                status["ping"] = f"error: {e}"
                status["connected"] = False
                
        return status
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.debug(f"Error closing Redis connection: {e}")
            finally:
                self.client = None
                self.connected = False


# Global Redis cache instance
redis_cache = RedisCache()


async def get_redis_cache() -> RedisCache:
    """
    Get or initialize the Redis cache instance.
    
    Returns:
        RedisCache instance
    """
    if not redis_cache._init_attempted:
        await redis_cache.initialize()
    return redis_cache


async def cache_public_reach_page(handle: str, data: Dict[str, Any]) -> bool:
    """
    Cache public reach page data (convenience function).
    
    Args:
        handle: Identity handle
        data: Page data to cache
        
    Returns:
        True if cached successfully, False otherwise
    """
    cache = await get_redis_cache()
    return await cache.set_public_reach_page(handle, data)


async def get_cached_public_reach_page(handle: str) -> Optional[Dict[str, Any]]:
    """
    Get cached public reach page data (convenience function).
    
    Args:
        handle: Identity handle
        
    Returns:
        Cached data or None if not found
    """
    cache = await get_redis_cache()
    return await cache.get_public_reach_page(handle)


async def invalidate_cached_public_reach_page(handle: str) -> bool:
    """
    Invalidate cached public reach page (convenience function).
    
    Args:
        handle: Identity handle
        
    Returns:
        True if invalidated successfully, False otherwise
    """
    cache = await get_redis_cache()
    return await cache.invalidate_public_reach_page(handle)


async def cache_health_check() -> Dict[str, Any]:
    """
    Check cache health status (convenience function).
    
    Returns:
        Dictionary with health information
    """
    cache = await get_redis_cache()
    return await cache.health_check()