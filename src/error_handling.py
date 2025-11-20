"""
Error Handling Utilities
Comprehensive error handling with retry logic and user-friendly messages
"""

import time
import functools
from typing import Callable, Any, Optional, Type
from datetime import datetime


class ErrorHandler:
    """Centralized error handling with retry logic"""
    
    @staticmethod
    def retry_on_failure(
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        Decorator for retrying functions on failure
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay on each retry
            exceptions: Tuple of exceptions to catch and retry
            on_retry: Optional callback function called on each retry
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries:
                            if on_retry:
                                on_retry(attempt + 1, max_retries, str(e))
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            # Last attempt failed
                            raise
                    except Exception as e:
                        # Non-retryable exception
                        raise
                
                # Should never reach here, but just in case
                if last_exception:
                    raise last_exception
                    
            return wrapper
        return decorator
    
    @staticmethod
    def handle_database_error(func: Callable) -> Callable:
        """Decorator for handling database errors"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                
                if "no such table" in error_msg:
                    raise ValueError(f"Database table not found. Please ensure database is initialized. Original error: {str(e)}")
                elif "no such column" in error_msg:
                    raise ValueError(f"Database column not found. Database schema may be outdated. Original error: {str(e)}")
                elif "database is locked" in error_msg:
                    raise RuntimeError(f"Database is locked. Please try again in a moment. Original error: {str(e)}")
                elif "disk i/o error" in error_msg:
                    raise RuntimeError(f"Database I/O error. Check disk space and permissions. Original error: {str(e)}")
                else:
                    raise RuntimeError(f"Database error: {str(e)}")
        
        return wrapper
    
    @staticmethod
    def handle_api_error(func: Callable) -> Callable:
        """Decorator for handling API errors"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                
                if "rate limit" in error_msg or "429" in error_msg:
                    raise RuntimeError("API rate limit exceeded. Please wait a moment and try again.")
                elif "authentication" in error_msg or "401" in error_msg or "403" in error_msg:
                    raise ValueError("API authentication failed. Please check your API key.")
                elif "timeout" in error_msg:
                    raise RuntimeError("API request timed out. Please try again.")
                elif "connection" in error_msg or "network" in error_msg:
                    raise RuntimeError("Network error. Please check your internet connection.")
                else:
                    raise RuntimeError(f"API error: {str(e)}")
        
        return wrapper
    
    @staticmethod
    def safe_execute(func: Callable, default_return: Any = None, log_error: bool = True) -> Any:
        """
        Safely execute a function and return default value on error
        
        Args:
            func: Function to execute
            default_return: Value to return on error
            log_error: Whether to log the error
        """
        try:
            return func()
        except Exception as e:
            if log_error:
                print(f"⚠️  Error in {func.__name__}: {str(e)}")
            return default_return


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message in user-friendly way
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # User-friendly error messages
    friendly_messages = {
        "ValueError": "Invalid input provided",
        "KeyError": "Required data not found",
        "TypeError": "Data type mismatch",
        "FileNotFoundError": "File not found",
        "PermissionError": "Permission denied",
        "ConnectionError": "Connection failed",
        "TimeoutError": "Operation timed out",
    }
    
    base_message = friendly_messages.get(error_type, "An error occurred")
    
    if context:
        return f"{base_message} ({context}): {error_msg}"
    else:
        return f"{base_message}: {error_msg}"


def validate_lead_id(lead_id: str) -> bool:
    """Validate lead ID format"""
    if not lead_id or not isinstance(lead_id, str):
        return False
    # Lead IDs can be numeric or start with #
    return lead_id.strip() != ""


def validate_status(status: str) -> bool:
    """Validate status value"""
    valid_statuses = ["Won", "Lost", "Contacted", "Oppurtunity", "Disputed", "won", "lost", "contacted", "opportunity", "disputed"]
    return status in valid_statuses


def validate_budget(budget: float) -> bool:
    """Validate budget value"""
    return isinstance(budget, (int, float)) and budget >= 0


def sanitize_input(value: Any, max_length: Optional[int] = None) -> str:
    """Sanitize user input"""
    if value is None:
        return ""
    
    value_str = str(value).strip()
    
    if max_length and len(value_str) > max_length:
        value_str = value_str[:max_length]
    
    # Remove potentially dangerous characters
    value_str = value_str.replace(";", "").replace("--", "")
    
    return value_str

