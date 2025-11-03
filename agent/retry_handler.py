"""
Retry mechanism for transient failures in the Accessibility Testing Agent.
Provides exponential backoff and configurable retry policies.
"""

import asyncio
import time
from typing import Callable, TypeVar, Optional, Tuple, Any
from functools import wraps
from .exceptions import RetryableError, TransientNavigationError, TransientAnalysisError
from .logger import setup_logger

logger = setup_logger("retry_handler")

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 2,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay


class RetryHandler:
    """Handles retry logic for operations that may fail transiently."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    async def retry_async(
        self,
        func: Callable,
        *args,
        retryable_exceptions: Tuple[type, ...] = (RetryableError,),
        **kwargs
    ) -> Any:
        """
        Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exception types that should trigger retry
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of successful function call
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    delay = self.config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {type(e).__name__}: {str(e)}",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": self.config.max_retries + 1,
                            "retry_delay": delay,
                            "error_type": type(e).__name__
                        }
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.config.max_retries + 1} attempts exhausted",
                        extra={
                            "max_attempts": self.config.max_retries + 1,
                            "error_type": type(e).__name__
                        }
                    )
            
            except Exception as e:
                # Non-retryable exception, raise immediately
                logger.error(
                    f"Non-retryable error: {type(e).__name__}: {str(e)}",
                    extra={"error_type": type(e).__name__}
                )
                raise
        
        # If we get here, all retries were exhausted
        raise last_exception
    
    def retry_sync(
        self,
        func: Callable,
        *args,
        retryable_exceptions: Tuple[type, ...] = (RetryableError,),
        **kwargs
    ) -> Any:
        """
        Retry a sync function with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Positional arguments for func
            retryable_exceptions: Tuple of exception types that should trigger retry
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of successful function call
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    delay = self.config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {type(e).__name__}: {str(e)}",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": self.config.max_retries + 1,
                            "retry_delay": delay,
                            "error_type": type(e).__name__
                        }
                    )
                    
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.config.max_retries + 1} attempts exhausted",
                        extra={
                            "max_attempts": self.config.max_retries + 1,
                            "error_type": type(e).__name__
                        }
                    )
            
            except Exception as e:
                # Non-retryable exception, raise immediately
                logger.error(
                    f"Non-retryable error: {type(e).__name__}: {str(e)}",
                    extra={"error_type": type(e).__name__}
                )
                raise
        
        # If we get here, all retries were exhausted
        raise last_exception


def with_retry(
    max_retries: int = 2,
    initial_delay: float = 1.0,
    retryable_exceptions: Tuple[type, ...] = (RetryableError,)
):
    """
    Decorator for adding retry logic to async functions.
    
    Usage:
        @with_retry(max_retries=3, initial_delay=2.0)
        async def my_function():
            # ... code that may fail transiently
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(max_retries=max_retries, initial_delay=initial_delay)
            handler = RetryHandler(config)
            return await handler.retry_async(func, *args, retryable_exceptions=retryable_exceptions, **kwargs)
        return wrapper
    return decorator


# Default retry handler instance
default_retry_handler = RetryHandler()
