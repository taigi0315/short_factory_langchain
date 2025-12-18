"""
Centralized error handling for API routes.
Provides consistent logging, monitoring, and fallback behavior.
"""
import structlog
from functools import wraps
from typing import Callable, TypeVar
from fastapi import HTTPException

logger = structlog.get_logger()

T = TypeVar('T')


def with_fallback(mock_data_fn: Callable[..., T]):
    """
    Decorator that wraps API endpoint with standardized error handling.

    Args:
        mock_data_fn: Function that returns mock data for fallback

    Usage:
        @with_fallback(lambda req: get_mock_stories())
        async def generate_stories(request):
            # implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the error with full context
                logger.error(
                    f"Error in {func.__name__}: {str(e)} (args: {str(args)[:100]})",
                    exc_info=True
                )

                # Return mock data for verification platform
                logger.warning(f"Falling back to mock data for {func.__name__}")
                # Extract the request parameter (first arg or from kwargs)
                # This handles both dependency injection and non-DI routes
                request = kwargs.get('request', args[0] if args else None)
                return mock_data_fn(request) if request else mock_data_fn()

        return wrapper
    return decorator


def strict_error_handling(func: Callable) -> Callable:
    """
    Decorator for endpoints that should NOT fallback to mock data.
    Raises proper HTTPException instead.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Client error - bad request
            logger.warning(f"Bad request in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Server error
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return wrapper
