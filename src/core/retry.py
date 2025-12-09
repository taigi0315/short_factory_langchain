import asyncio
import functools
import structlog
import random
from typing import Callable, Type, Tuple, Optional, Union, Any
from src.core.config import settings

logger = structlog.get_logger()

class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        jitter: bool = True
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        self.jitter = jitter

def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults from settings if None)
        operation_name: Name for logging (uses function name if None)
    
    Example:
        @retry_with_backoff(RetryConfig(max_retries=5))
        async def generate_image(prompt: str):
            return await api.generate(prompt)
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use provided config or defaults from settings
            # We resolve defaults here to ensure we pick up the latest settings
            nonlocal config
            if config is None:
                # We'll use a default config based on settings if not provided
                # Note: We can't easily access settings defaults here if they aren't passed in,
                # so we rely on the caller or default to reasonable values if settings are missing attributes.
                # Ideally, we'd pull from settings here.
                
                # Let's try to pull from settings if available, otherwise defaults
                max_retries = getattr(settings, 'DEFAULT_MAX_RETRIES', 3)
                initial_delay = getattr(settings, 'DEFAULT_RETRY_INITIAL_DELAY', 1.0)
                max_delay = getattr(settings, 'DEFAULT_RETRY_MAX_DELAY', 60.0)
                exponential_base = getattr(settings, 'DEFAULT_RETRY_EXPONENTIAL_BASE', 2.0)
                
                config = RetryConfig(
                    max_retries=max_retries,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base
                )

            op_name = operation_name or func.__name__
            last_error = None
            
            for attempt in range(1, config.max_retries + 1):
                try:
                    if attempt > 1:
                        logger.info(
                            f"Attempting {op_name}",
                            attempt=attempt,
                            max_retries=config.max_retries
                        )
                    
                    result = await func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(
                            f"{op_name} succeeded after retry",
                            attempt=attempt
                        )
                    
                    return result
                    
                except config.retryable_exceptions as e:
                    last_error = e
                    
                    # If we've reached max retries, re-raise
                    if attempt == config.max_retries:
                        logger.error(
                            f"{op_name} failed after all retries",
                            total_attempts=config.max_retries,
                            final_error=str(e),
                            error_type=type(e).__name__
                        )
                        raise
                    
                    logger.warning(
                        f"{op_name} failed",
                        attempt=attempt,
                        max_retries=config.max_retries,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    # Calculate backoff delay
                    delay = min(
                        config.initial_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )
                    
                    # Add jitter if enabled (randomize between 0.5 * delay and 1.5 * delay)
                    if config.jitter:
                        delay = delay * random.uniform(0.5, 1.5)
                    
                    logger.info(
                        f"Waiting before retry",
                        wait_seconds=f"{delay:.2f}",
                        next_attempt=attempt + 1
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here due to the raise in the loop, but for type safety:
            if last_error:
                raise last_error
            raise RuntimeError("Unexpected retry loop exit")
        
        return wrapper
    return decorator
