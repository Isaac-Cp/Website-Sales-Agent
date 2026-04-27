"""
Performance optimization utilities for Render free tier.
Helps reduce memory, CPU, and network usage.
"""

import time
import functools
import config


# Simple in-memory cache with TTL
_CACHE = {}
_CACHE_TIMES = {}


def cache_get(key):
    """Retrieve value from cache if not expired."""
    if key not in _CACHE:
        return None
    
    created_at = _CACHE_TIMES.get(key, 0)
    if time.time() - created_at > config.DASHBOARD_CACHE_SECONDS:
        cache_delete(key)
        return None
    
    return _CACHE[key]


def cache_set(key, value):
    """Store value in cache with TTL."""
    _CACHE[key] = value
    _CACHE_TIMES[key] = time.time()


def cache_delete(key):
    """Remove value from cache."""
    _CACHE.pop(key, None)
    _CACHE_TIMES.pop(key, None)


def cache_clear():
    """Clear entire cache."""
    global _CACHE, _CACHE_TIMES
    _CACHE = {}
    _CACHE_TIMES = {}


def cacheable(func):
    """Decorator to cache function results with TTL."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and args
        cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
        
        # Try cache first
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        
        # Compute and cache
        result = func(*args, **kwargs)
        cache_set(cache_key, result)
        return result
    
    return wrapper


def time_operation(operation_name):
    """Context manager to log operation timing."""
    class TimingContext:
        def __init__(self, name):
            self.name = name
            self.start = None
        
        def __enter__(self):
            self.start = time.time()
            return self
        
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            if config.is_resource_constrained and elapsed > 2:
                print(f"⏱️ [{self.name}] took {elapsed:.1f}s on free tier")
            elif elapsed > 5:
                print(f"⚠️ [{self.name}] took {elapsed:.1f}s")
    
    return TimingContext(operation_name)


def estimate_memory(obj):
    """Rough estimate of object memory usage."""
    import sys
    
    if isinstance(obj, (list, tuple)):
        return sys.getsizeof(obj) + sum(estimate_memory(item) for item in obj)
    elif isinstance(obj, dict):
        return sys.getsizeof(obj) + sum(
            estimate_memory(k) + estimate_memory(v) 
            for k, v in obj.items()
        )
    else:
        return sys.getsizeof(obj)


# Connection pooling helpers
_CONNECTION_POOL = {}


def get_pool_size():
    """Get current pool size."""
    return len(_CONNECTION_POOL)


def clear_pool():
    """Clear connection pool."""
    global _CONNECTION_POOL
    for conn in _CONNECTION_POOL.values():
        try:
            conn.close()
        except:
            pass
    _CONNECTION_POOL = {}


# Email validation caching
_VALIDATION_CACHE = {}


def get_cached_validation(email):
    """Get cached email validation result."""
    return _VALIDATION_CACHE.get(email.lower())


def cache_validation(email, result):
    """Cache email validation result."""
    _VALIDATION_CACHE[email.lower()] = result


def clear_old_validations(max_size=1000):
    """Limit validation cache size to prevent memory leaks."""
    if len(_VALIDATION_CACHE) > max_size:
        # Remove oldest half
        to_remove = list(_VALIDATION_CACHE.keys())[:max_size // 2]
        for key in to_remove:
            _VALIDATION_CACHE.pop(key, None)
