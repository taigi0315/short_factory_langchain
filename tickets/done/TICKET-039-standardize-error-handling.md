# [TICKET-039] Standardize Error Handling and Retry Logic Across Agents

## Priority
- [ ] Critical (System stability, security, data loss risk)
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [x] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [x] Technical Debt
- [x] Code Duplication

## Impact Assessment

**Business Impact:**
- **Reliability**: Inconsistent error handling leads to unpredictable failures
- **Debugging**: Different error patterns make troubleshooting difficult
- **User Experience**: Inconsistent retry behavior affects reliability
- **Maintenance**: Duplicated retry logic increases maintenance burden

**Technical Impact:**
- **Modules Affected**: All 7 agents + API routes
- **Files to Change**: ~12 files
- **Code Reduction**: ~50 lines of duplicated retry logic
- **Breaking Changes**: Minimal (internal refactoring)

**Effort Estimate:**
- Medium (2-3 days)

## Problem Description

### Current State

**Location**: Retry logic duplicated in:
- `src/agents/image_gen/agent.py:73-148` (retry with exponential backoff)
- `src/agents/script_writer/agent.py:208-270` (retry with validation)
- `src/agents/story_finder/agent.py:230-252` (basic retry via LangChain)

**Problematic Pattern 1** (from image_gen/agent.py:73-148):
```python
# Generate images one by one to enable incremental checkpoints
for scene in scenes:
    # Retry logic: up to 3 attempts with exponential backoff
    max_retries = 3
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Generating images for scene (attempt {}/{})".format(attempt, max_retries),
                scene_number=scene.scene_number,
                attempt=attempt
            )
            
            scene_image_paths = await self._generate_scene_images(client, scene)
            image_paths[scene.scene_number] = scene_image_paths
            
            # Success! Break out of retry loop
            logger.info(
                "Images generated successfully",
                scene_number=scene.scene_number,
                count=len(scene_image_paths),
                attempt=attempt
            )
            break
            
        except Exception as e:
            last_error = e
            logger.warning(
                "Image generation failed for scene (attempt {}/{})".format(attempt, max_retries),
                scene_number=scene.scene_number,
                attempt=attempt,
                error=str(e),
                error_type=type(e).__name__
            )
            
            if attempt == max_retries:
                logger.error(
                    "All retry attempts exhausted for scene",
                    scene_number=scene.scene_number,
                    total_attempts=max_retries,
                    final_error=str(e)
                )
                raise RuntimeError(
                    f"Image generation failed for scene {scene.scene_number} after {max_retries} attempts: {e}"
                ) from e
            else:
                # Wait before retrying (exponential backoff: 2s, 4s)
                wait_time = 2 ** attempt
                logger.info(
                    f"Waiting {wait_time}s before retry...",
                    scene_number=scene.scene_number,
                    wait_seconds=wait_time
                )
                await asyncio.sleep(wait_time)
```

**Problematic Pattern 2** (from script_writer/agent.py:208-270):
```python
last_error = None

for attempt in range(max_retries):
    try:
        # Invoke the chain
        result = self.chain.invoke({
            "subject": subject,
            "language": language,
            "max_video_scenes": max_video_scenes,
            "min_scenes": settings.MIN_SCENES
        })
        
        # Validate and fix the script
        result = self._validate_and_fix_script(result)
        
        logger.info(
            f"[{request_id}] Script generation completed successfully "
            f"(attempt {attempt + 1}/{max_retries}). "
            f"Generated script with {len(result.scenes)} scenes."
        )
        
        return result
        
    except ValidationError as e:
        last_error = e
        logger.warning(
            f"[{request_id}] Validation error on attempt {attempt + 1}/{max_retries}: {str(e)}"
        )
        
        if attempt < max_retries - 1:
            logger.info(f"[{request_id}] Retrying script generation...")
        else:
            logger.error(
                f"[{request_id}] All retry attempts exhausted. "
                f"Script generation failed with validation errors."
            )
```

**Issues with Current Approach:**
1. **Duplicated Logic**: Same retry pattern copied 3+ times
2. **Inconsistent Backoff**: Different backoff strategies (exponential vs none)
3. **Inconsistent Logging**: Different log formats and levels
4. **No Circuit Breaker**: No protection against cascading failures
5. **Hardcoded Values**: Retry counts and delays hardcoded

### Root Cause Analysis

**Why does this problem exist?**
- Each agent implemented retry logic independently
- No shared retry infrastructure
- Copy-paste development
- No standardization guidelines

**Pattern that led to this issue:**
1. First agent (image_gen) implemented retry logic
2. Other agents copied the pattern
3. Minor variations introduced over time
4. No refactoring to extract common logic

### Evidence

**Retry Logic Occurrences:**
- image_gen/agent.py: Lines 73-148 (~75 lines)
- script_writer/agent.py: Lines 208-270 (~62 lines)
- LangChain built-in: max_retries parameter (implicit)

**Duplication Metrics:**
- Total duplicated lines: ~137 lines
- Unique logic: ~30 lines
- Duplication ratio: 78%

**Inconsistencies:**
- Backoff strategy: Exponential (2^n) vs None
- Max retries: 3 vs configurable
- Error types: RuntimeError vs original exception
- Logging format: Different across agents

## Proposed Solution

### Approach

**High-level strategy:**
1. Create reusable `@retry_with_backoff` decorator
2. Standardize error logging
3. Add circuit breaker for external services
4. Extract retry configuration to settings
5. Migrate all agents to use decorator

### Implementation Details

**Step 1: Create Retry Decorator** (`src/core/retry.py`):

```python
import asyncio
import functools
import structlog
from typing import Callable, Type, Tuple, Optional
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
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults if None)
        operation_name: Name for logging (uses function name if None)
    
    Example:
        @retry_with_backoff(RetryConfig(max_retries=5))
        async def generate_image(prompt: str):
            return await api.generate(prompt)
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            last_error = None
            
            for attempt in range(1, config.max_retries + 1):
                try:
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
                    
                    logger.warning(
                        f"{op_name} failed",
                        attempt=attempt,
                        max_retries=config.max_retries,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    if attempt == config.max_retries:
                        logger.error(
                            f"{op_name} failed after all retries",
                            total_attempts=config.max_retries,
                            final_error=str(e)
                        )
                        raise
                    
                    # Calculate backoff delay
                    delay = min(
                        config.initial_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )
                    
                    logger.info(
                        f"Waiting before retry",
                        wait_seconds=delay,
                        next_attempt=attempt + 1
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_error
        
        return wrapper
    return decorator
```

**Step 2: Add Retry Settings** (`src/core/config.py`):

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Retry Configuration
    DEFAULT_MAX_RETRIES: int = Field(default=3, ge=1, le=10)
    DEFAULT_RETRY_INITIAL_DELAY: float = Field(default=1.0, ge=0.1, le=10.0)
    DEFAULT_RETRY_MAX_DELAY: float = Field(default=60.0, ge=1.0, le=300.0)
    DEFAULT_RETRY_EXPONENTIAL_BASE: float = Field(default=2.0, ge=1.1, le=10.0)
```

**Step 3: Refactor ImageGenAgent** (example):

```python
from src.core.retry import retry_with_backoff, RetryConfig

class ImageGenAgent:
    def __init__(self):
        self.retry_config = RetryConfig(
            max_retries=settings.DEFAULT_MAX_RETRIES,
            initial_delay=settings.DEFAULT_RETRY_INITIAL_DELAY,
            max_delay=settings.DEFAULT_RETRY_MAX_DELAY
        )
    
    async def generate_images(self, scenes, workflow_id=None):
        """Generate images for scenes with retry logic."""
        image_paths = {}
        
        for scene in scenes:
            # Use decorator for retry logic
            scene_image_paths = await self._generate_scene_images_with_retry(
                client, scene
            )
            image_paths[scene.scene_number] = scene_image_paths
            
            # Save checkpoint
            if workflow_manager and scene_image_paths:
                workflow_manager.save_image(
                    workflow_id, scene.scene_number, scene_image_paths[0]
                )
        
        return image_paths
    
    @retry_with_backoff(operation_name="image generation")
    async def _generate_scene_images_with_retry(self, client, scene):
        """Generate images for a single scene (with automatic retry)."""
        return await self._generate_scene_images(client, scene)
```

**Step 4: Create Circuit Breaker** (optional, for external services):

```python
class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    Opens circuit after consecutive failures, preventing cascading failures.
    """
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        name: str = "circuit"
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                logger.info(f"Circuit breaker {self.name} entering half-open state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is open"
                )
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} closed")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker {self.name} opened",
                    failure_count=self.failure_count
                )
            
            raise
```

### Alternative Approaches Considered

**Option 1: Use tenacity library**
- Use existing retry library (tenacity)
- **Why not chosen**: Adds external dependency, less control

**Option 2: LangChain built-in retries only**
- Rely on LangChain's max_retries parameter
- **Why not chosen**: Doesn't work for non-LLM operations

**Option 3: No standardization**
- Keep current approach
- **Why not chosen**: Maintenance burden, inconsistency

### Benefits

- **Consistency**: All agents use same retry logic
- **Maintainability**: Changes in one place
- **Configurability**: Retry behavior configurable via settings
- **Observability**: Standardized logging for debugging
- **Resilience**: Circuit breaker prevents cascading failures

### Risks & Considerations

- **Breaking Changes**: Agents must be refactored
- **Testing**: Need to test retry behavior
- **Configuration**: Need to tune retry parameters

## Testing Strategy

### Unit Tests

```python
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
    
    @retry_with_backoff(RetryConfig(max_retries=3))
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
    @retry_with_backoff(RetryConfig(max_retries=3))
    async def operation():
        raise ValueError("Permanent error")
    
    with pytest.raises(ValueError):
        await operation()
```

## Files Affected

### New Files
- `src/core/retry.py` - Retry decorator and circuit breaker
- `tests/unit/test_retry.py` - Retry logic tests

### Modified Files
- `src/core/config.py` - Add retry settings
- `src/agents/image_gen/agent.py` - Use retry decorator
- `src/agents/script_writer/agent.py` - Use retry decorator
- `src/agents/voice/agent.py` - Use retry decorator
- `src/agents/video_gen/agent.py` - Use retry decorator

## Dependencies

- **Depends on**: TICKET-036 (Base Class - can add retry to base)
- **Blocks**: None
- **Related to**: TICKET-041 (Configuration)

## Success Criteria

- [ ] Retry decorator created and tested
- [ ] All agents use standardized retry logic
- [ ] Retry configuration in settings
- [ ] Circuit breaker implemented (optional)
- [ ] ~50 lines of duplicated code removed
- [ ] All tests pass
- [ ] Documentation updated

---

**Estimated Effort**: 2-3 days  
**Priority**: High  
**Risk**: Medium  
**ROI**: High (consistency, maintainability, resilience)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **Resilience**: A distributed system (even a modular one like this) needs robust handling of transient failures.
- **Observability**: Standardizing how we log errors and retries makes debugging production issues much easier.
- **Simplicity**: Moving complex retry loops out of business logic and into a decorator cleans up the core agent code significantly.

**Implementation Phase:** Phase 2 - Reliability & Standardization
**Sequence Order:** #4 in implementation queue (After Base Class and Config)

**Architectural Guidance:**
Key considerations for implementation:
- **Decorator vs Base Class Method**: The decorator approach (`@retry_with_backoff`) is flexible and pythonic. However, consider if `BaseAgent` should expose a helper method `execute_with_retry` that uses this decorator internally, to further simplify usage for subclasses.
- **Circuit Breaker**: This is a "nice to have" for now. Focus on the retry logic first. Only implement Circuit Breaker if we have distinct external services that fail hard (like an API going down for hours).
- **Exceptions**: Be specific about *what* exceptions trigger a retry. Don't retry on `ValueError` (logic error), but do retry on `ConnectionError` or `Timeout`.

**Dependencies:**
- **Must complete first**: TICKET-036 (Base Class) - Ideally, we integrate this into the base class or use it within the refactored agents.
- **Should complete first**: TICKET-041 (Config) - So the retry settings are pulled from the centralized config.
- **Blocks**: None

**Risk Mitigation:**
- **Infinite Loops**: Ensure `max_retries` is always enforced.
- **Thundering Herd**: The exponential backoff helps, but adding a small "jitter" (randomness) to the delay is a best practice to prevent all agents retrying at the exact same millisecond.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Retry logic includes "jitter" to prevent thundering herd.
- [ ] Logs include a correlation ID (if available) to trace retries across logs.

**Alternative Approaches Considered:**
- **Selected approach:** Custom decorator with `structlog` integration.

**Implementation Notes:**
- Implement `src/core/retry.py` first.
- Add unit tests for the decorator itself before applying it to agents.

**Estimated Timeline**: 2-3 days
**Recommended Owner**: Senior Backend Engineer
