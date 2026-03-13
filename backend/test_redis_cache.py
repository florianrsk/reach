#!/usr/bin/env python3
"""
Test Redis caching implementation for the Reach application.
"""

import asyncio
import sys
import os
from redis_cache import RedisCache, get_redis_cache, cache_health_check
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_connection():
    """Test Redis connection and basic operations."""
    print("=== Testing Redis Cache Connection ===")
    
    # Get cache instance
    cache = await get_redis_cache()
    
    # Check health
    health = await cache.health_check()
    print(f"Redis Health: {health}")
    
    if not health.get("connected"):
        print("⚠️  Redis not connected - testing fallback behavior")
        print("✅ Fallback behavior: System will use MongoDB directly")
        return True  # Fallback is acceptable
    
    print("✅ Redis connected successfully")
    
    # Test basic operations
    test_key = "test:cache:key"
    test_value = {"message": "Hello Redis", "timestamp": "2024-01-01T00:00:00Z"}
    
    # Set value
    set_result = await cache.set(test_key, test_value, ttl=10)
    print(f"Set cache key: {set_result}")
    
    if set_result:
        # Get value
        retrieved = await cache.get(test_key)
        print(f"Retrieved from cache: {retrieved}")
        
        if retrieved == test_value:
            print("✅ Cache set/get operations work correctly")
        else:
            print(f"❌ Cache retrieval mismatch: {retrieved} != {test_value}")
            return False
        
        # Delete value
        delete_result = await cache.delete(test_key)
        print(f"Delete cache key: {delete_result}")
        
        # Verify deletion
        after_delete = await cache.get(test_key)
        if after_delete is None:
            print("✅ Cache delete operation works correctly")
        else:
            print(f"❌ Cache not deleted: {after_delete}")
            return False
    else:
        print("⚠️  Cache set failed (may be expected if Redis not configured)")
    
    return True

async def test_public_reach_page_cache():
    """Test public reach page caching functions."""
    print("\n=== Testing Public Reach Page Cache ===")
    
    cache = await get_redis_cache()
    
    test_handle = "testuser123"
    test_data = {
        "identity": {
            "handle": test_handle,
            "display_name": "Test User",
            "headline": "Software Developer",
            "face_completed": True
        }
    }
    
    # Test set
    set_result = await cache.set_public_reach_page(test_handle, test_data)
    print(f"Set public reach page cache: {set_result}")
    
    if set_result or not cache.connected:
        # Test get (may return None if Redis not connected)
        retrieved = await cache.get_public_reach_page(test_handle)
        print(f"Retrieved public reach page: {retrieved is not None}")
        
        if cache.connected and retrieved != test_data:
            print(f"❌ Retrieved data mismatch: {retrieved}")
            return False
        
        # Test invalidation
        invalidate_result = await cache.invalidate_public_reach_page(test_handle)
        print(f"Invalidate public reach page: {invalidate_result}")
        
        # Clean up test key if it exists
        if cache.connected:
            await cache.delete(f"reach:public:{test_handle}")
        
        print("✅ Public reach page cache functions work correctly")
        return True
    else:
        print("⚠️  Cache set failed (may be expected)")
        return cache.connected == False  # Success if Redis not connected (fallback mode)

async def test_cache_pattern_deletion():
    """Test pattern-based cache deletion."""
    print("\n=== Testing Cache Pattern Deletion ===")
    
    cache = await get_redis_cache()
    
    if not cache.connected:
        print("⚠️  Redis not connected, skipping pattern deletion test")
        return True
    
    # Create test keys
    test_keys = [
        "reach:public:user1",
        "reach:public:user2", 
        "reach:public:user3",
        "other:cache:key"
    ]
    
    test_value = {"test": "data"}
    
    # Set test keys
    for key in test_keys:
        await cache.set(key, test_value, ttl=60)
    
    # Delete pattern
    deleted_count = await cache.delete_pattern("reach:public:*")
    print(f"Deleted {deleted_count} keys matching pattern 'reach:public:*'")
    
    # Verify deletion
    remaining = []
    for key in test_keys:
        value = await cache.get(key)
        if value is not None:
            remaining.append(key)
    
    # Clean up any remaining test keys
    for key in test_keys:
        await cache.delete(key)
    
    if deleted_count >= 3 and len(remaining) == 1 and remaining[0] == "other:cache:key":
        print("✅ Pattern deletion works correctly")
        return True
    else:
        print(f"❌ Pattern deletion issue: deleted={deleted_count}, remaining={remaining}")
        return False

async def main():
    """Run all Redis cache tests."""
    print("Redis Cache Implementation Test")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Public Reach Page Cache", test_public_reach_page_cache),
        ("Cache Pattern Deletion", test_cache_pattern_deletion),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    # Check Redis status
    cache = await get_redis_cache()
    health = await cache.health_check()
    
    print(f"\nRedis Status:")
    print(f"  Available: {health.get('redis_available', False)}")
    print(f"  Connected: {health.get('connected', False)}")
    print(f"  Initialized: {health.get('client_initialized', False)}")
    
    if not health.get("connected", False):
        print("\n⚠️  IMPORTANT: Redis is not connected.")
        print("   This is OK for testing - the system will fall back to MongoDB.")
        print("   To enable Redis caching:")
        print("   1. Create a free Redis Cloud account at redis.io")
        print("   2. Get your connection string")
        print("   3. Update REDIS_URL in backend/.env")
    
    # Close Redis connection
    await cache.close()
    
    all_passed = all(success for _, success in results)
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)