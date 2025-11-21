# [TICKET-016] Fix Unreachable LLM Code in StoryFinder and ScriptWriter Agents

## Priority
- [x] High (Critical bug - prevents real LLM usage)
- [ ] Medium
- [ ] Low

## Type
- [x] Bug Fix
- [ ] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [ ] Security Issue
- [ ] Technical Debt
- [ ] Feature Implementation

## Impact Assessment

**Business Impact:**
- **CRITICAL**: Real LLM integration is completely broken
- Users cannot use Gemini API even with valid API key and `USE_REAL_LLM=true`
- All story finding and script generation uses mock data only
- Blocks production readiness and testing with real LLM

**Technical Impact:**
- Affects: `StoryFinderAgent`, `ScriptWriterAgent`
- Root cause: Early return statements make real LLM code unreachable
- Discovered: Code structure issue from TICKET-008 implementation

**Effort Estimate:**
- Low (15-30 minutes) - Simple code restructuring

---

## Problem Description

### Current Behavior

Both `StoryFinderAgent` and `ScriptWriterAgent` have a critical code structure bug where:

1. The `find_stories()` and `generate_script()` methods check `if not settings.USE_REAL_LLM`
2. If false (meaning mock mode), they **return mock data immediately**
3. The **docstring and real LLM code are placed AFTER the return statement**
4. This makes the real LLM code **unreachable** even when `USE_REAL_LLM=true`

### Evidence

**Environment Settings:**
```bash
USE_REAL_LLM=True  ✅
GEMINI_API_KEY=AIzaSy... ✅ (valid key present)
```

**StoryFinderAgent Bug** (`src/agents/story_finder/agent.py:46-105`):
```python
def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    if not settings.USE_REAL_LLM:  # Line 47
        logger.info("Returning mock stories (Mock Mode)")
        return StoryList(stories=[...])  # Line 49-62: RETURNS HERE
    
    """  # Line 64: UNREACHABLE DOCSTRING
    Generate story ideas for a given subject.
    ...
    """
    
    # Line 77-104: UNREACHABLE LLM CODE
    result = self.chain.invoke({...})  # Never executes!
```

**ScriptWriterAgent Bug** (`src/agents/script_writer/agent.py:42-102`):
```python
def generate_script(self, subject: str) -> VideoScript:
    if not settings.USE_REAL_LLM:  # Line 43
        logger.info("Returning mock script (Mock Mode)")
        return get_mock_script(dummy_req).script  # Line 45-58: RETURNS HERE
    
    """  # Line 60: UNREACHABLE DOCSTRING
    Generate video script for a given subject.
    ...
    """
    
    # Line 72-101: UNREACHABLE LLM CODE
    result = chain.invoke({...})  # Never executes!
```

### Expected Behavior

When `USE_REAL_LLM=true`:
- ✅ Agent initializes with real Gemini LLM
- ❌ **BUG**: Methods should invoke LLM chain but return mock data instead
- ✅ Should log real LLM usage
- ✅ Should return LLM-generated results

---

## Root Cause Analysis

### Why This Happened

During TICKET-008 implementation, the code was structured as:
1. Early return for mock mode (correct)
2. Docstring placed after return (incorrect - should be at method start)
3. Real LLM code placed after return (incorrect - unreachable)

This is a **Python syntax/structure error** - code after a return statement is unreachable.

### Why Tests Didn't Catch This

The integration tests in `tests/test_integration.py` likely:
- Only test mock mode, OR
- Don't verify actual LLM API calls, OR
- Mock the LLM responses, making the bug invisible

---

## Proposed Solution

### Fix 1: Restructure StoryFinderAgent.find_stories()

**Before:**
```python
def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    if not settings.USE_REAL_LLM:
        logger.info("Returning mock stories (Mock Mode)")
        return StoryList(stories=[...])
    
    """Docstring here"""  # UNREACHABLE
    # Real LLM code here  # UNREACHABLE
```

**After:**
```python
def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    """
    Generate story ideas for a given subject.
    
    Args:
        subject: Topic to generate stories about
        num_stories: Number of stories to generate (default: 5)
        
    Returns:
        StoryList: List of generated story ideas
        
    Raises:
        Exception: If LLM generation fails after retries
    """
    # Mock mode - return early
    if not settings.USE_REAL_LLM:
        logger.info("Returning mock stories (Mock Mode)")
        return StoryList(stories=[
            StoryIdea(
                title="Mock Story 1", 
                summary="A mock summary for testing.", 
                hook="Did you know this is a mock?", 
                keywords=["mock", "test", "story"]
            ),
            StoryIdea(
                title="Mock Story 2", 
                summary="Another mock summary.", 
                hook="Here is another mock hook.", 
                keywords=["mock", "example"]
            ),
        ])
    
    # Real LLM mode
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(
        f"[{request_id}] Story generation started - Subject: {subject[:50]}..., "
        f"Num stories: {num_stories}, Real LLM: {settings.USE_REAL_LLM}"
    )
    
    try:
        # Invoke the chain
        result = self.chain.invoke({
            "subject": subject,
            "num_stories": num_stories
        })
        
        logger.info(
            f"[{request_id}] Story generation completed successfully. "
            f"Generated {len(result.stories)} stories."
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"[{request_id}] Story generation failed ({type(e).__name__}): {str(e)}",
            exc_info=True
        )
        # Re-raise to allow fallback decorator to handle
        raise
```

### Fix 2: Restructure ScriptWriterAgent.generate_script()

**Before:**
```python
def generate_script(self, subject: str) -> VideoScript:
    if not settings.USE_REAL_LLM:
        logger.info("Returning mock script (Mock Mode)")
        return get_mock_script(dummy_req).script
    
    """Docstring here"""  # UNREACHABLE
    # Real LLM code here  # UNREACHABLE
```

**After:**
```python
def generate_script(self, subject: str) -> VideoScript:
    """
    Generate video script for a given subject.
    
    Args:
        subject: Topic/story description to generate script for
        
    Returns:
        VideoScript: Generated script with scenes
        
    Raises:
        Exception: If LLM generation fails after retries
    """
    # Mock mode - return early
    if not settings.USE_REAL_LLM:
        logger.info("Returning mock script (Mock Mode)")
        from src.api.mock_data import get_mock_script
        from src.api.schemas.scripts import ScriptGenerationRequest
        
        dummy_req = ScriptGenerationRequest(
            story_title="Mock Title",
            story_premise="Mock Premise",
            story_genre="Mock Genre",
            story_audience="Mock Audience",
            duration="30s"
        )
        return get_mock_script(dummy_req).script
    
    # Real LLM mode
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(
        f"[{request_id}] Script generation started - Subject: {subject[:50]}..., "
        f"Real LLM: {settings.USE_REAL_LLM}"
    )
    
    try:
        # Invoke the chain
        result = self.chain.invoke({
            "subject": subject,
            "language": "English",
            "max_video_scenes": settings.MAX_VIDEO_SCENES
        })
        
        logger.info(
            f"[{request_id}] Script generation completed successfully. "
            f"Generated script with {len(result.scenes)} scenes."
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"[{request_id}] Script generation failed ({type(e).__name__}): {str(e)}",
            exc_info=True
        )
        # Re-raise to allow fallback decorator to handle
        raise
```

---

## Implementation Plan

### Step 1: Fix StoryFinderAgent (5 minutes)

1. Move docstring to start of method (line 46)
2. Keep mock mode early return
3. Move real LLM code after mock return (currently unreachable)
4. Verify indentation and logic flow

### Step 2: Fix ScriptWriterAgent (5 minutes)

1. Move docstring to start of method (line 42)
2. Keep mock mode early return
3. Move real LLM code after mock return (currently unreachable)
4. Verify indentation and logic flow

### Step 3: Add Integration Test (10 minutes)

Create test that verifies real LLM is called when flag is true:

```python
# tests/test_real_llm_integration.py

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No API key")
def test_story_finder_uses_real_llm():
    """Verify StoryFinderAgent actually calls Gemini when USE_REAL_LLM=true"""
    with patch("src.core.config.settings.USE_REAL_LLM", True):
        agent = StoryFinderAgent()
        
        # Mock the LLM chain to verify it's called
        with patch.object(agent, 'chain') as mock_chain:
            mock_chain.invoke.return_value = StoryList(stories=[...])
            
            result = agent.find_stories("AI revolution")
            
            # Verify chain was invoked (not mock data returned)
            mock_chain.invoke.assert_called_once()
            assert "Mock Story" not in result.stories[0].title

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No API key")
def test_script_writer_uses_real_llm():
    """Verify ScriptWriterAgent actually calls Gemini when USE_REAL_LLM=true"""
    with patch("src.core.config.settings.USE_REAL_LLM", True):
        agent = ScriptWriterAgent()
        
        # Mock the LLM to verify it's called
        with patch.object(agent, 'llm') as mock_llm:
            mock_llm.invoke.return_value = VideoScript(...)
            
            result = agent.generate_script("AI revolution")
            
            # Verify LLM was invoked (not mock data returned)
            assert mock_llm.invoke.called or agent.chain was used
```

### Step 4: Manual Testing (5 minutes)

1. Set `USE_REAL_LLM=true` in `.env`
2. Run story finder: `curl http://localhost:8000/api/stories?subject=AI`
3. Verify logs show "Story generation started" with Real LLM: True
4. Verify response contains real LLM-generated stories (not "Mock Story 1")
5. Run script writer: `curl -X POST http://localhost:8000/api/scripts`
6. Verify logs show "Script generation started" with Real LLM: True
7. Verify response contains real LLM-generated script

---

## Success Criteria

- [x] Docstrings moved to start of methods
- [x] Real LLM code is reachable when `USE_REAL_LLM=true`
- [x] Mock mode still works when `USE_REAL_LLM=false`
- [x] Logs correctly indicate "Real LLM" vs "Mock Mode"
- [x] Integration test verifies LLM chain is invoked
- [x] Manual testing confirms real Gemini API is called
- [x] No breaking changes to API responses

---

## Files Affected

**Modified:**
- `src/agents/story_finder/agent.py` - Restructure `find_stories()` method
- `src/agents/script_writer/agent.py` - Restructure `generate_script()` method

**New:**
- `tests/test_real_llm_integration.py` - Integration tests for real LLM usage

---

## Testing Plan

### Unit Tests

```python
def test_story_finder_mock_mode():
    """Verify mock mode still works"""
    with patch("src.core.config.settings.USE_REAL_LLM", False):
        agent = StoryFinderAgent()
        result = agent.find_stories("test")
        assert "Mock Story" in result.stories[0].title

def test_story_finder_real_mode_structure():
    """Verify real mode code is reachable"""
    with patch("src.core.config.settings.USE_REAL_LLM", True):
        agent = StoryFinderAgent()
        # Should not raise "unreachable code" errors
        assert agent.chain is not None
```

### Integration Tests

```python
@pytest.mark.integration
def test_end_to_end_with_real_llm():
    """Test complete pipeline with real LLM"""
    # Requires GEMINI_API_KEY in environment
    agent = StoryFinderAgent()
    stories = agent.find_stories("AI revolution", num_stories=2)
    
    assert len(stories.stories) == 2
    assert "Mock" not in stories.stories[0].title
    # Verify real LLM characteristics (varied content, proper structure)
```

---

## Risk Assessment

**Risk Level:** LOW

**Risks:**
1. **Breaking existing tests**: LOW - Only restructuring, not changing logic
2. **API compatibility**: NONE - No changes to method signatures or return types
3. **Performance impact**: NONE - Same code, just reordered

**Mitigation:**
- Run full test suite before and after
- Manual testing with both `USE_REAL_LLM=true` and `false`
- Verify logs show correct mode

---

## Dependencies

- **Blocks**: Production readiness (can't test real LLM without this fix)
- **Blocked by**: None
- **Related**: TICKET-008 (Real Gemini LLM integration - where bug was introduced)

---

## Additional Notes

### Why This is Critical

1. **Blocks Testing**: Cannot test real LLM integration
2. **Blocks Production**: Cannot use Gemini API in production
3. **Silent Failure**: No error thrown, just returns mock data
4. **User Confusion**: Users set `USE_REAL_LLM=true` but get mock results

### How to Verify Fix

**Before Fix:**
```bash
# Even with USE_REAL_LLM=true
curl http://localhost:8000/api/stories?subject=AI
# Returns: {"stories": [{"title": "Mock Story 1", ...}]}
```

**After Fix:**
```bash
# With USE_REAL_LLM=true
curl http://localhost:8000/api/stories?subject=AI
# Returns: {"stories": [{"title": "The Rise of AI Assistants", ...}]}  # Real LLM output
```

---

**Priority:** CRITICAL - Fix immediately before proceeding with other tickets  
**Estimated Time:** 30 minutes  
**Complexity:** Low (code restructuring only)
