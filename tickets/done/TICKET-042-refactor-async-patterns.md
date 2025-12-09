# [TICKET-042] Refactor Async Patterns for Consistency

## Priority
- [ ] Critical
- [ ] High
- [x] Medium
- [ ] Low

## Type
- [x] Refactoring
- [x] Performance Optimization

## Impact Assessment

**Business Impact**: Better performance, more consistent behavior

**Technical Impact**:
- Modules Affected: Agents, API routes
- Files to Change: ~12 files
- Performance Improvement: ~20% better throughput
- Breaking Changes: Minimal

**Effort Estimate**: Medium (3-4 days)

## Problem Description

### Current State

**Issue 1: Sync methods that should be async**

```python
# Currently sync, blocks event loop
def _download_sync(self, url: str, filepath: str):
    response = requests.get(url, timeout=10)
    # ...

# Should be async
async def _download(self, url: str, filepath: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # ...
```

**Issue 2: Inconsistent async error handling**

```python
# Some places
try:
    result = await operation()
except Exception as e:
    logger.error("Failed", error=str(e))
    raise

# Other places
try:
    result = await operation()
except Exception as e:
    logger.error("Failed", error=str(e))
    return None  # Inconsistent!
```

**Issue 3: Missing async context managers**

```python
# Currently
client = GeminiImageClient(api_key)
result = await client.generate_image(prompt)
# No cleanup

# Should be
async with GeminiImageClient(api_key) as client:
    result = await client.generate_image(prompt)
# Automatic cleanup
```

## Proposed Solution

### Implementation

**1. Convert sync I/O to async**:

```python
import aiohttp
import aiofiles

class ImageGenAgent:
    async def _download(self, url: str, filepath: str):
        """Async download with proper error handling."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(await response.read())
```

**2. Add async context managers**:

```python
class GeminiImageClient:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def generate_image(self, prompt: str):
        async with self.session.post(url, json=data) as response:
            return await response.json()
```

**3. Standardize async error handling**:

```python
# Use consistent pattern
async def operation():
    try:
        result = await risky_operation()
        return result
    except SpecificError as e:
        logger.error("Operation failed", error=str(e))
        raise  # Always re-raise, don't swallow
```

**4. Add async timeouts**:

```python
import asyncio

async def operation_with_timeout():
    try:
        result = await asyncio.wait_for(
            slow_operation(),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        raise
```

## Files Affected

- `src/agents/image_gen/agent.py` - Convert sync downloads to async
- `src/agents/image_gen/gemini_image_client.py` - Add async context manager
- `src/agents/voice/agent.py` - Standardize async patterns
- `src/agents/video_gen/agent.py` - Add async timeouts
- `requirements.txt` - Add aiohttp, aiofiles

## Dependencies

- **Depends on**: None
- **Blocks**: None
- **Related to**: TICKET-039 (Error Handling)

## Success Criteria

- [ ] All sync I/O converted to async
- [ ] Async context managers implemented
- [ ] Consistent error handling
- [ ] Async timeouts added
- [ ] Performance improved by ~20%
- [ ] All tests pass

---

**Estimated Effort**: 3-4 days  
**Priority**: Medium  
**Risk**: Medium  
**ROI**: Medium (performance, consistency)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **Scalability**: Blocking the event loop with sync I/O (like `requests` or `open()`) kills the concurrency benefits of FastAPI/asyncio. This is a critical fix for throughput.
- **Resource Management**: Async context managers (`__aenter__`/`__aexit__`) ensure resources like network connections are closed properly, preventing leaks.

**Implementation Phase:** Phase 3 - Performance & Validation
**Sequence Order:** #7 in implementation queue

**Architectural Guidance:**
Key considerations for implementation:
- **Libraries**: Use `aiohttp` for HTTP and `aiofiles` for file I/O.
- **Session Management**: Do NOT create a new `ClientSession` for every request. Create one per application or per agent lifecycle and reuse it. This is a common performance pitfall.
- **Timeouts**: Always set timeouts. Infinite waits are the enemy of stability.

**Dependencies:**
- **Must complete first**: None
- **Should complete first**: TICKET-039 (Error Handling) - Async error handling should follow the standardized pattern.
- **Blocks**: None

**Risk Mitigation:**
- **Deadlocks**: Be careful with mixing sync and async code. Avoid `asyncio.run()` inside an already running loop.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Verify no `requests` library usage remains in the hot path.
- [ ] Verify `ClientSession` is reused, not recreated per request.

**Alternative Approaches Considered:**
- **Selected approach:** Full async conversion.

**Implementation Notes:**
- Refactor `GeminiImageClient` to accept a session or manage one efficiently.

**Estimated Timeline**: 3-4 days
**Recommended Owner**: Senior Backend Engineer
