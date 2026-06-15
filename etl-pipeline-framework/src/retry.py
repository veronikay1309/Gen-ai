import time
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Decorator that retries a function call on failure using exponential backoff.

    Args:
        max_attempts: Maximum number of total attempts (including first try).
        backoff_factor: Base delay in seconds (doubles each retry: 2s, 4s, 8s...).

    Usage:
        @with_retry(max_attempts=3, backoff_factor=2)
        def my_flaky_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = backoff_factor ** (attempt - 1)
                        logger.warning(
                            f"[Retry {attempt}/{max_attempts}] '{func.__name__}' failed: {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[Retry {attempt}/{max_attempts}] '{func.__name__}' failed after "
                            f"{max_attempts} attempts: {str(e)}"
                        )
            raise last_exception
        return wrapper
    return decorator
