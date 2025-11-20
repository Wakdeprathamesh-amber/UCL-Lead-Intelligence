"""
Query Caching Module
TTL-based caching for frequent queries to improve performance
"""

import time
import hashlib
import json
from typing import Any, Optional, Callable, Dict
from functools import wraps
from collections import OrderedDict


class QueryCache:
    """TTL-based query cache with LRU eviction"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of cached items (LRU eviction)
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()  # OrderedDict for LRU
        self.timestamps = {}  # Track when items were cached
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function name and arguments"""
        # Create a stable representation of arguments
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else []
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key not in self.cache:
            return None
        
        # Check if expired
        if key in self.timestamps:
            age = time.time() - self.timestamps[key]
            if age > self.default_ttl:
                # Expired, remove it
                del self.cache[key]
                del self.timestamps[key]
                return None
        
        # Move to end (most recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache with TTL"""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.timestamps:
                del self.timestamps[oldest_key]
        
        # Add new item
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        self.timestamps.clear()
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries
        
        Args:
            pattern: Optional pattern to match (if None, clears all)
        
        Returns:
            Number of items invalidated
        """
        if pattern is None:
            count = len(self.cache)
            self.clear()
            return count
        
        # Remove matching keys
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
        
        return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "items": [
                {
                    "key": key,
                    "age_seconds": time.time() - self.timestamps.get(key, 0)
                }
                for key in list(self.cache.keys())[:10]  # First 10 items
            ]
        }


# Global cache instance
_global_cache = QueryCache(max_size=100, default_ttl=300)


def cached(ttl: Optional[int] = None, cache_instance: Optional[QueryCache] = None):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time-to-live in seconds (uses cache default if None)
        cache_instance: Cache instance to use (uses global if None)
    
    Example:
        @cached(ttl=600)
        def expensive_query():
            return database.query()
    """
    cache = cache_instance or _global_cache
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Not in cache, compute value
            value = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, value, ttl=ttl)
            
            return value
        
        # Add cache control methods to function
        wrapper.cache_clear = lambda: cache.invalidate(func.__name__)
        wrapper.cache_stats = lambda: cache.get_stats()
        
        return wrapper
    
    return decorator


def get_cache() -> QueryCache:
    """Get the global cache instance"""
    return _global_cache


def clear_cache(pattern: Optional[str] = None) -> int:
    """Clear cache entries (optionally matching a pattern)"""
    return _global_cache.invalidate(pattern)


if __name__ == "__main__":
    # Test cache
    cache = QueryCache(max_size=5, default_ttl=10)
    
    print("Testing Query Cache...")
    
    # Test set/get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    print("✅ Set/Get working")
    
    # Test expiration
    cache.set("key2", "value2", ttl=1)
    time.sleep(2)
    assert cache.get("key2") is None
    print("✅ TTL expiration working")
    
    # Test LRU eviction
    for i in range(6):
        cache.set(f"key{i}", f"value{i}")
    assert "key0" not in cache.cache  # Oldest should be evicted
    print("✅ LRU eviction working")
    
    # Test decorator
    @cached(ttl=5)
    def expensive_function(x):
        print(f"Computing for {x}...")
        return x * 2
    
    result1 = expensive_function(5)
    result2 = expensive_function(5)  # Should use cache
    assert result1 == result2 == 10
    print("✅ Decorator working")
    
    print("\n✅ All cache tests passed!")

