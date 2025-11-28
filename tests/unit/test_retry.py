import pytest
import asyncio
from src.core.retry import retry_with_backoff, RetryConfig

@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    """Test successful operation on first attempt."""
    call_count = 0
    
    @retry_with_backoff()
    async def operation():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await operation()
    assert result == "success"
    assert call_count == 1

@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test successful operation after retries."""
    call_count = 0
    
    config = RetryConfig(max_retries=3, initial_delay=0.01) # Low delay for fast tests
    
    @retry_with_backoff(config)
    async def operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"
    
    result = await operation()
    assert result == "success"
    assert call_count == 3

@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test all retries exhausted."""
    call_count = 0
    config = RetryConfig(max_retries=3, initial_delay=0.01)
    
    @retry_with_backoff(config)
    async def operation():
        nonlocal call_count
        call_count += 1
        raise ValueError("Permanent error")
    
    with pytest.raises(ValueError):
        await operation()
    
    assert call_count == 3

@pytest.mark.asyncio
async def test_retry_specific_exception():
    """Test retrying only specific exceptions."""
    call_count = 0
    config = RetryConfig(
        max_retries=3, 
        initial_delay=0.01,
        retryable_exceptions=(ValueError,)
    )
    
    @retry_with_backoff(config)
    async def operation():
        nonlocal call_count
        call_count += 1
        raise TypeError("Not retryable")
    
    with pytest.raises(TypeError):
        await operation()
    
    assert call_count == 1  # Should fail immediately
