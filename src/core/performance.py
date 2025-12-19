"""
Performance monitoring and profiling utilities.

Provides decorators and utilities to track operation performance,
log execution times, and identify bottlenecks.
"""
import time
import functools
import structlog
from typing import Callable, Any, TypeVar, cast
from contextlib import contextmanager

logger = structlog.get_logger()

T = TypeVar('T')


def log_performance(operation_name: str):
    """
    Decorator to log operation performance with timing information.

    Logs the duration of function execution and any errors that occur.
    Useful for identifying performance bottlenecks in the application.

    Args:
        operation_name: Human-readable name for the operation being timed

    Returns:
        Decorated function that logs performance metrics

    Example:
        @log_performance("script generation")
        async def generate_script(self, subject: str) -> VideoScript:
            # ... implementation ...
            pass

        # Logs: "script generation completed in 2.34s"
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            operation_id = f"{operation_name}_{id(args)}"

            logger.info(
                f"{operation_name} started",
                operation=operation_name,
                operation_id=operation_id
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    operation_id=operation_id,
                    duration_seconds=f"{duration:.2f}",
                    success=True
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation_name} failed",
                    operation=operation_name,
                    operation_id=operation_id,
                    duration_seconds=f"{duration:.2f}",
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False,
                    exc_info=True
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            operation_id = f"{operation_name}_{id(args)}"

            logger.info(
                f"{operation_name} started",
                operation=operation_name,
                operation_id=operation_id
            )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    operation_id=operation_id,
                    duration_seconds=f"{duration:.2f}",
                    success=True
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation_name} failed",
                    operation=operation_name,
                    operation_id=operation_id,
                    duration_seconds=f"{duration:.2f}",
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False,
                    exc_info=True
                )
                raise

        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return cast(Callable[..., T], async_wrapper)
        else:
            return cast(Callable[..., T], sync_wrapper)

    return decorator


@contextmanager
def track_time(operation_name: str):
    """
    Context manager to track execution time of a code block.

    Args:
        operation_name: Name of the operation being tracked

    Yields:
        None

    Example:
        with track_time("database query"):
            result = db.query(...)
    """
    start_time = time.time()
    logger.debug(f"{operation_name} started")

    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(
            f"{operation_name} completed",
            operation=operation_name,
            duration_seconds=f"{duration:.2f}"
        )


class PerformanceMonitor:
    """
    Class for collecting and reporting performance metrics.

    Tracks operation durations and provides summary statistics.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = {}

    def record(self, operation: str, duration: float) -> None:
        """
        Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

    def get_summary(self) -> dict[str, dict[str, float]]:
        """
        Get summary statistics for all recorded operations.

        Returns:
            Dictionary mapping operation names to statistics
            (count, total, average, min, max)
        """
        summary = {}
        for operation, durations in self.metrics.items():
            if durations:
                summary[operation] = {
                    'count': len(durations),
                    'total_seconds': sum(durations),
                    'avg_seconds': sum(durations) / len(durations),
                    'min_seconds': min(durations),
                    'max_seconds': max(durations)
                }
        return summary

    def log_summary(self) -> None:
        """Log summary statistics for all operations."""
        summary = self.get_summary()
        if summary:
            logger.info("Performance summary", metrics=summary)
        else:
            logger.info("No performance metrics recorded")

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self.metrics.clear()


# Global performance monitor instance
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    return _monitor
