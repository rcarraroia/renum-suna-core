#!/usr/bin/env python3
"""
Test script for Redis migration validation.

This script tests Redis functionality after migration from aioredis to redis.asyncio
including connection, basic operations, pub/sub, and performance.
"""

import asyncio
import time
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from services.redis import (
        initialize_async, close, get_client,
        set, get, delete, publish, create_pubsub,
        rpush, lrange, keys, expire
    )
    REDIS_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import Redis service: {e}")
    REDIS_SERVICE_AVAILABLE = False

try:
    import redis.asyncio as redis
    REDIS_ASYNCIO_AVAILABLE = True
except ImportError:
    print("❌ redis.asyncio not available")
    REDIS_ASYNCIO_AVAILABLE = False


class RedisTestSuite:
    """Comprehensive Redis test suite."""
    
    def __init__(self):
        self.test_results = []
        self.client = None
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    async def test_redis_import(self):
        """Test that redis.asyncio can be imported."""
        try:
            import redis.asyncio as redis
            self.log_test("Redis Import", True, "redis.asyncio imported successfully")
            return True
        except ImportError as e:
            self.log_test("Redis Import", False, f"Import failed: {e}")
            return False
    
    async def test_redis_service_import(self):
        """Test that Redis service can be imported."""
        if REDIS_SERVICE_AVAILABLE:
            self.log_test("Redis Service Import", True, "Redis service imported successfully")
            return True
        else:
            self.log_test("Redis Service Import", False, "Redis service import failed")
            return False
    
    async def test_direct_connection(self):
        """Test direct Redis connection."""
        try:
            # Test direct connection without password first
            client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await client.ping()
            await client.aclose()
            self.log_test("Direct Connection (no auth)", True, "Connected successfully")
            return True
        except Exception as e:
            # Try with password
            try:
                client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    password='secure_redis_password',
                    decode_responses=True
                )
                await client.ping()
                await client.aclose()
                self.log_test("Direct Connection (with auth)", True, "Connected with password")
                return True
            except Exception as e2:
                self.log_test("Direct Connection", False, f"Connection failed: {e2}")
                return False
    
    async def test_service_connection(self):
        """Test Redis service connection."""
        if not REDIS_SERVICE_AVAILABLE:
            self.log_test("Service Connection", False, "Redis service not available")
            return False
        
        try:
            client = await initialize_async()
            if client:
                self.client = client
                self.log_test("Service Connection", True, "Service connected successfully")
                return True
            else:
                self.log_test("Service Connection", False, "Service connection returned None")
                return False
        except Exception as e:
            self.log_test("Service Connection", False, f"Service connection failed: {e}")
            return False
    
    async def test_basic_operations(self):
        """Test basic Redis operations."""
        if not self.client:
            self.log_test("Basic Operations", False, "No Redis client available")
            return False
        
        try:
            # Test SET/GET
            test_key = "test:migration:basic"
            test_value = "Hello Redis Migration!"
            
            await set(test_key, test_value, ex=60)
            retrieved_value = await get(test_key)
            
            if retrieved_value == test_value:
                self.log_test("Basic SET/GET", True, "SET/GET operations working")
            else:
                self.log_test("Basic SET/GET", False, f"Expected '{test_value}', got '{retrieved_value}'")
                return False
            
            # Test DELETE
            await delete(test_key)
            deleted_value = await get(test_key)
            
            if deleted_value is None:
                self.log_test("Basic DELETE", True, "DELETE operation working")
            else:
                self.log_test("Basic DELETE", False, f"Key still exists after delete: {deleted_value}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Basic Operations", False, f"Operations failed: {e}")
            return False
    
    async def test_list_operations(self):
        """Test Redis list operations."""
        if not self.client:
            self.log_test("List Operations", False, "No Redis client available")
            return False
        
        try:
            list_key = "test:migration:list"
            
            # Clear any existing list
            await delete(list_key)
            
            # Test RPUSH
            await rpush(list_key, "item1", "item2", "item3")
            
            # Test LRANGE
            items = await lrange(list_key, 0, -1)
            
            expected_items = ["item1", "item2", "item3"]
            if items == expected_items:
                self.log_test("List Operations", True, f"List operations working: {items}")
            else:
                self.log_test("List Operations", False, f"Expected {expected_items}, got {items}")
                return False
            
            # Cleanup
            await delete(list_key)
            return True
            
        except Exception as e:
            self.log_test("List Operations", False, f"List operations failed: {e}")
            return False
    
    async def test_pubsub_functionality(self):
        """Test Redis Pub/Sub functionality."""
        if not self.client:
            self.log_test("Pub/Sub", False, "No Redis client available")
            return False
        
        try:
            channel = "test:migration:pubsub"
            test_message = "Hello Pub/Sub!"
            
            # Create pubsub
            pubsub = await create_pubsub()
            await pubsub.subscribe(channel)
            
            # Publish message
            await publish(channel, test_message)
            
            # Wait for message with timeout
            message_received = False
            for _ in range(10):  # Try for 1 second
                message = await pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    if message['data'] == test_message:
                        message_received = True
                        break
                await asyncio.sleep(0.1)
            
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            
            if message_received:
                self.log_test("Pub/Sub", True, "Pub/Sub functionality working")
                return True
            else:
                self.log_test("Pub/Sub", False, "Message not received")
                return False
            
        except Exception as e:
            self.log_test("Pub/Sub", False, f"Pub/Sub failed: {e}")
            return False
    
    async def test_key_expiration(self):
        """Test Redis key expiration."""
        if not self.client:
            self.log_test("Key Expiration", False, "No Redis client available")
            return False
        
        try:
            exp_key = "test:migration:expire"
            
            # Set key with short expiration
            await set(exp_key, "expire_me", ex=1)
            
            # Check key exists
            value = await get(exp_key)
            if value != "expire_me":
                self.log_test("Key Expiration", False, "Key not set properly")
                return False
            
            # Wait for expiration
            await asyncio.sleep(1.5)
            
            # Check key expired
            expired_value = await get(exp_key)
            if expired_value is None:
                self.log_test("Key Expiration", True, "Key expiration working")
                return True
            else:
                self.log_test("Key Expiration", False, f"Key did not expire: {expired_value}")
                return False
            
        except Exception as e:
            self.log_test("Key Expiration", False, f"Expiration test failed: {e}")
            return False
    
    async def test_performance(self):
        """Test Redis performance."""
        if not self.client:
            self.log_test("Performance", False, "No Redis client available")
            return False
        
        try:
            # Test multiple operations
            num_operations = 100
            start_time = time.time()
            
            for i in range(num_operations):
                key = f"test:migration:perf:{i}"
                await set(key, f"value_{i}", ex=60)
            
            for i in range(num_operations):
                key = f"test:migration:perf:{i}"
                await get(key)
            
            for i in range(num_operations):
                key = f"test:migration:perf:{i}"
                await delete(key)
            
            end_time = time.time()
            duration = end_time - start_time
            ops_per_second = (num_operations * 3) / duration  # 3 operations per iteration
            
            if ops_per_second > 100:  # Reasonable performance threshold
                self.log_test("Performance", True, f"{ops_per_second:.0f} ops/sec")
                return True
            else:
                self.log_test("Performance", False, f"Low performance: {ops_per_second:.0f} ops/sec")
                return False
            
        except Exception as e:
            self.log_test("Performance", False, f"Performance test failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup test resources."""
        try:
            if self.client:
                # Clean up any remaining test keys
                test_keys = await keys("test:migration:*")
                if test_keys:
                    for key in test_keys:
                        await delete(key)
            
            # Close Redis service connection
            await close()
            self.log_test("Cleanup", True, "Resources cleaned up")
        except Exception as e:
            self.log_test("Cleanup", False, f"Cleanup failed: {e}")
    
    async def run_all_tests(self):
        """Run all Redis tests."""
        print("=== Redis Migration Test Suite ===\n")
        
        tests = [
            self.test_redis_import,
            self.test_redis_service_import,
            self.test_direct_connection,
            self.test_service_connection,
            self.test_basic_operations,
            self.test_list_operations,
            self.test_pubsub_functionality,
            self.test_key_expiration,
            self.test_performance
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Test crashed: {e}")
        
        # Cleanup
        await self.cleanup()
        
        # Summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All Redis tests passed! Migration successful.")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check Redis configuration.")
            return False


async def main():
    """Main test runner."""
    test_suite = RedisTestSuite()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())