#!/usr/bin/env python3
"""
Error handling utilities for Project Authentica.
Provides standardized error handling and custom exceptions.
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, Callable, TypeVar, ParamSpec

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic function handling
P = ParamSpec("P")
R = TypeVar("R")

class AuthenticaError(Exception):
    """Base exception class for Project Authentica."""
    pass

class ConfigurationError(AuthenticaError):
    """Exception raised for configuration errors."""
    pass

class DatabaseError(AuthenticaError):
    """Exception raised for database errors."""
    pass

class RedditAPIError(AuthenticaError):
    """Exception raised for Reddit API errors."""
    pass

class LLMError(AuthenticaError):
    """Exception raised for LLM API errors."""
    pass

def handle_exceptions(func: Callable[P, R]) -> Callable[P, Optional[R]]:
    """
    Decorator for standardized exception handling.
    
    Args:
        func: The function to wrap with exception handling
        
    Returns:
        A wrapped function that handles exceptions
    """
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        try:
            return func(*args, **kwargs)
        except AuthenticaError as e:
            # Log known application errors
            logger.error(f"{e.__class__.__name__}: {str(e)}")
            return None
        except Exception as e:
            # Log unexpected errors with stack trace
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None
    return wrapper

def log_error_context(error: Exception, context: Dict[str, Any]) -> None:
    """
    Log an error with additional context information.
    
    Args:
        error (Exception): The error that occurred
        context (Dict[str, Any]): Additional context information
    """
    error_type = error.__class__.__name__
    error_message = str(error)
    
    # Format context as key-value pairs
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    
    logger.error(f"{error_type}: {error_message} | Context: {context_str}")
    logger.debug(f"Stack trace: {traceback.format_exc()}")

def is_critical_error(error: Exception) -> bool:
    """
    Determine if an error is critical and should stop execution.
    
    Args:
        error (Exception): The error to evaluate
        
    Returns:
        bool: True if the error is critical, False otherwise
    """
    # Configuration errors are critical
    if isinstance(error, ConfigurationError):
        return True
    
    # Database errors might be critical depending on the operation
    if isinstance(error, DatabaseError):
        # Check error message for indicators of critical failures
        error_msg = str(error).lower()
        if any(keyword in error_msg for keyword in ["connection", "corrupt", "permission"]):
            return True
    
    # Reddit API errors might be critical if they indicate authentication issues
    if isinstance(error, RedditAPIError):
        error_msg = str(error).lower()
        if any(keyword in error_msg for keyword in ["auth", "credential", "permission", "rate limit"]):
            return True
    
    return False 