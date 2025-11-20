"""
Rate Limiter Module
Implements rate limiting with exponential backoff for API calls
"""

import time
from functools import wraps
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """Thread-safe rate limiter with exponential backoff"""
    
    def __init__(self, max_calls: int = 60, period: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
        self.backoff_multiplier = 1.5
        self.max_backoff = 60  # Maximum backoff in seconds
    
    def _clean_old_calls(self, key: str):
        """Remove calls older than the period"""
        current_time = time.time()
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if current_time - call_time < self.period
        ]
    
    def is_allowed(self, key: str = "default") -> tuple[bool, Optional[float]]:
        """
        Check if a call is allowed
        
        Returns:
            (is_allowed, wait_time): Tuple of (allowed status, seconds to wait if not allowed)
        """
        with self.lock:
            self._clean_old_calls(key)
            
            if len(self.calls[key]) < self.max_calls:
                self.calls[key].append(time.time())
                return True, None
            
            # Calculate wait time
            oldest_call = min(self.calls[key])
            wait_time = self.period - (time.time() - oldest_call)
            
            # Apply exponential backoff
            consecutive_failures = len(self.calls[key]) - self.max_calls + 1
            backoff = min(
                wait_time * (self.backoff_multiplier ** consecutive_failures),
                self.max_backoff
            )
            
            return False, max(0, backoff)
    
    def wait_if_needed(self, key: str = "default"):
        """Wait if rate limit is exceeded"""
        allowed, wait_time = self.is_allowed(key)
        if not allowed and wait_time:
            time.sleep(wait_time)
            # Retry once after waiting
            allowed, _ = self.is_allowed(key)
            if not allowed:
                raise RuntimeError(f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.")


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_calls: int = 60, period: int = 60) -> RateLimiter:
    """Get or create global rate limiter"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(max_calls=max_calls, period=period)
    return _global_rate_limiter


def rate_limited(max_calls: int = 60, period: int = 60, key: str = "default"):
    """
    Decorator for rate limiting functions
    
    Args:
        max_calls: Maximum calls per period
        period: Time period in seconds
        key: Rate limit key (for different limits per function)
    """
    def decorator(func):
        limiter = get_rate_limiter(max_calls=max_calls, period=period)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed(key=key)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

