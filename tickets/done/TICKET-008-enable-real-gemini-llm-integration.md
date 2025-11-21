# [TICKET-008] Enable Real Gemini LLM Integration with Production Config

## Priority
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [x] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [ ] Technical Debt
- [ ] Code Duplication
- [x] Feature Implementation

## Impact Assessment
**Business Impact:**
- **HIGH**: Enables real AI-powered story and script generation (core product feature)
- Currently using fallback mock data or failing silently
- Real LLM generates much higher quality, contextually relevant content
- Required for production launch

**Technical Impact:**
- Affects: `StoryFinderAgent`, `ScriptWriterAgent`
- Requires: Valid GEMINI_API_KEY configuration
- Cost implications: ~$0.001-0.01 per video generation
- API rate limits: 15 RPM (requests per minute) for free tier

**Effort Estimate:**
- Small (< 1 day) - 4-6 hours including testing

---

## Problem Description

### Current State
**Status:** Partially implemented but not production-ready

**What works:**
- ✅ `StoryFinderAgent` and `ScriptWriterAgent` have Gemini integration code
- ✅ Settings has `GEMINI_API_KEY` field
- ✅ `USE_REAL_LLM` flag exists

**What's missing:**
1. **No API key validation** - Silent failures if key is invalid
2. **No error handling** - Retries fail indefinitely, no timeout
3. **No model validation** - Using `gemini-1.5-flash` which may change
4. **No cost tracking** - Can't monitor API usage
5. **No rate limit handling** - Will fail on quota exceeded
6. **No response validation** - Malformed LLM responses not caught
7. **No fallback strategy** - Should degrade gracefully if API is down

**Current Error:**
```
WARNING: Retrying langchain_google_genai.chat_models._chat_with_retry in 2.0 seconds 
as it raised NotFound: 404 models/gemini-1.5-flash is not found for API version v1beta
```

This suggests either:
- API key is invalid/missing
- Model name is incorrect for the API version
- Need to use different endpoint

---

## Requirements

### Functional Requirements

**FR-1: API Key Management**
- System SHALL validate GEMINI_API_KEY on startup
- System SHALL provide clear error message if key is missing/invalid
- System SHALL support multiple API keys for load balancing (future)

**FR-2: Model Configuration**
- System SHALL use configurable model name (from settings)
- System SHALL validate model availability before first request
- System SHALL support fallback to different model if primary fails

**FR-3: Error Handling**
- System SHALL retry failed requests up to 3 times with exponential backoff
- System SHALL timeout requests after 30 seconds
- System SHALL log all API errors with full context
- System SHALL return mock data if all retries fail (graceful degradation)

**FR-4: Response Validation**
- System SHALL validate LLM response matches expected Pydantic schema
- System SHALL handle partial/incomplete responses
- System SHALL sanitize LLM output (remove potential unsafe content)

**FR-5: Cost & Usage Tracking**
- System SHALL log token usage for each request
- System SHALL estimate cost per request
- System SHALL track daily/monthly API spend
- System SHALL alert if approaching budget limits

---

### Non-Functional Requirements

**NFR-1: Performance**
- Story generation: < 5 seconds (P95)
- Script generation: < 10 seconds (P95)
- System SHALL cache repeated requests for 1 hour

**NFR-2: Reliability**
- API success rate: > 99% (excluding quota errors)
- System SHALL handle rate limits gracefully
- System SHALL work offline with mock data

**NFR-3: Security**
- API keys SHALL NOT be logged or exposed in responses
- System SHALL use HTTPS for all API calls
- System SHALL sanitize user input before sending to LLM

**NFR-4: Observability**
- All LLM calls SHALL be traced with request IDs
- Token usage SHALL be logged per request
- Errors SHALL include full stack trace in logs (not user-facing)

---

## Expected Behavior

### Test Cases

**TC-1: Successful Story Generation (Real LLM)**
```python
# Given
settings.USE_REAL_LLM = True
settings.GEMINI_API_KEY = "valid_key_here"

# When
agent = StoryFinderAgent()
stories = agent.find_stories("funny cat videos", num_stories=3)

# Then
assert len(stories.stories) == 3
assert all(story.title for story in stories.stories)
assert all(story.summary for story in stories.stories)
# Stories should be contextually relevant to "funny cat videos"
```

**TC-2: API Key Validation on Startup**
```python
# Given
settings.GEMINI_API_KEY = None

# When/Then
with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
    agent = StoryFinderAgent()
```

**TC-3: Graceful Degradation on API Failure**
```python
# Given
settings.GEMINI_API_KEY = "invalid_key"
settings.USE_REAL_LLM = True

# When
agent = StoryFinderAgent()
stories = agent.find_stories("cats")

# Then
# Should fall back to mock data after retries
assert len(stories.stories) > 0
# Should log warning about fallback
```

**TC-4: Rate Limit Handling**
```python
# Simulate: Make 20 rapid requests

# Expected: 
# - First 15 succeed (within rate limit)
# - Next 5 are queued/delayed
# - No requests fail with 429 error
```

**TC-5: Token Usage Logging**
```python
# Given
agent = StoryFinderAgent()

# When
stories = agent.find_stories("test topic")

# Then
# Logs should contain:
# INFO: LLM request completed. Tokens: input=50, output=200, total=250
# INFO: Estimated cost: $0.00025
```

**TC-6: Response Validation**
```python
# Given: LLM returns malformed JSON

# When
stories = agent.find_stories("topic")

# Then
# Should retry or fall back to mock
# Should log validation error
```

---

## Implementation Plan

### Phase 1: API Key Validation & Error Handling (2 hours)

**Step 1.1: Add startup validation**
```python
# src/agents/story_finder/agent.py
class StoryFinderAgent:
    def __init__(self):
        # Validate API key if real mode
        if settings.USE_REAL_LLM:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required when USE_REAL_LLM=true. "
                    "Set it in .env file or environment variables."
                )
            
            # Test API key validity
            try:
                self._validate_api_key()
            except Exception as e:
                logger.error(f"Invalid GEMINI_API_KEY: {e}")
                raise ValueError(f"GEMINI_API_KEY validation failed: {e}")
        
        # Initialize LLM...
```

**Step 1.2: Add retry configuration**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableConfig

self.llm = ChatGoogleGenerativeAI(
    model=settings.llm_model_name,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
    max_retries=3,
    timeout=30.0,
    # Add exponential backoff
    request_timeout=30,
)
```

**Step 1.3: Wrap chain invocation with error handling**
```python
def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    try:
        return self.chain.invoke({
            "subject": subject,
            "num_stories": num_stories
        })
    except Exception as e:
        logger.error(f"LLM generation failed: {e}", exc_info=True)
        
        # Fall back to mock data
        logger.warning("Falling back to mock story data")
        return self._generate_mock_stories(subject, num_stories)
```

---

### Phase 2: Model & Endpoint Configuration (1 hour)

**Step 2.1: Fix model name**  
Google Gemini models for LangChain:
- ✅ `gemini-1.5-pro` (best quality, slower, more expensive)
- ✅ `gemini-1.5-flash` (fast, cheaper - **recommended**)
- ✅ `gemini-pro` (older, stable)

Update if current model giving 404:
```python
# src/core/config.py
llm_model_name: str = Field(
    default="gemini-1.5-flash-latest",  # Use -latest suffix
    description="LLM model to use for text generation"
)
```

**Step 2.2: Add model availability check**
```python
def _validate_api_key(self):
    """Test API key by making a minimal request."""
    try:
        test_llm = ChatGoogleGenerativeAI(
            model=settings.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            max_retries=1,
            timeout=10.0,
        )
        # Simple test invocation
        test_llm.invoke("test")  
        logger.info(f"✓ Gemini API key validated. Model: {settings.llm_model_name}")
    except Exception as e:
        raise ValueError(f"API key validation failed: {e}")
```

---

### Phase 3: Cost Tracking & Observability (2 hours)

**Step 3.1: Add token usage callback**
```python
from langchain.callbacks import get_openai_callback  # Works for Google too

def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    with get_openai_callback() as cb:
        result = self.chain.invoke({...})
        
        # Log usage
        logger.info(
            f"LLM Usage - Tokens: {cb.total_tokens}, "
            f"Cost: ${cb.total_cost:.6f}"
        )
        
        # Store metrics (future: send to monitoring)
        self._track_usage(cb.total_tokens, cb.total_cost)
        
        return result
```

**Step 3.2: Add usage tracking**
```python
# src/core/usage_tracker.py
class UsageTracker:
    def __init__(self):
        self.daily_tokens = 0
        self.daily_cost = 0.0
        self.monthly_tokens = 0
        self.monthly_cost = 0.0
    
    def track(self, tokens: int, cost: float):
        self.daily_tokens += tokens
        self.daily_cost += cost
        # Persist to Redis/DB for production
    
    def check_budget(self):
        if self.daily_cost > settings.DAILY_BUDGET_LIMIT:
            raise BudgetExceededError("Daily API budget exceeded")
```

**Step 3.3: Add request logging**
```python
import uuid

def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] Story generation started", extra={
        "request_id": request_id,
        "subject": subject,
        "num_stories": num_stories,
        "use_real_llm": settings.USE_REAL_LLM,
    })
    
    try:
        result = self.chain.invoke({...})
        logger.info(f"[{request_id}] Story generation completed successfully")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] Story generation failed: {e}")
        raise
```

---

### Phase 4: Rate Limiting & Caching (1 hour)

**Step 4.1: Add rate limiter**
```python
from ratelimit import limits, sleep_and_retry

CALLS_PER_MINUTE = 15  # Gemini free tier limit

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=60)
def _call_llm(self, input_data):
    """Rate-limited LLM call."""
    return self.chain.invoke(input_data)
```

**Step 4.2: Add caching**
```python
from functools import lru_cache
import hashlib

def _cache_key(subject: str, num_stories: int) -> str:
    return hashlib.md5(f"{subject}:{num_stories}".encode()).hexdigest()

@lru_cache(maxsize=100)
def find_stories_cached(self, subject: str, num_stories: int = 5) -> StoryList:
    return self.find_stories(subject, num_stories)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_story_finder_real.py (NEW)
import pytest
from unittest.mock import patch, MagicMock

def test_api_key_required_when_real_mode():
    """Test that API key is required in real mode."""
    with patch('src.core.config.settings.USE_REAL_LLM', True):
        with patch('src.core.config.settings.GEMINI_API_KEY', None):
            with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
                StoryFinderAgent()

def test_mock_mode_works_without_api_key():
    """Test that mock mode doesn't require API key."""
    with patch('src.core.config.settings.USE_REAL_LLM', False):
        with patch('src.core.config.settings.GEMINI_API_KEY', None):
            agent = StoryFinderAgent()  # Should not raise
            assert agent is not None

def test_fallback_on_llm_failure():
    """Test graceful fallback when LLM fails."""
    agent = StoryFinderAgent()
    
    # Mock LLM to raise exception
    with patch.object(agent, 'chain') as mock_chain:
        mock_chain.invoke.side_effect = Exception("API Error")
        
        # Should fall back to mock data
        stories = agent.find_stories("test")
        assert len(stories.stories) > 0
```

### Integration Tests
```python
# tests/test_real_llm_integration.py (NEW)
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY for real API test"
)
def test_real_story_generation():
    """Integration test with real Gemini API."""
    agent = StoryFinderAgent()
    stories = agent.find_stories("space exploration", num_stories=2)
    
    assert len(stories.stories) == 2
    # Verify quality - stories should be relevant
    for story in stories.stories:
        assert "space" in story.summary.lower() or "exploration" in story.summary.lower()
```

### Manual Test Plan
1. **Setup**: Export valid `GEMINI_API_KEY` in `.env`
2. **Test 1 - Real Generation**:
   ```bash
   export USE_REAL_LLM=true
   python -c "from src.agents.story_finder.agent import StoryFinderAgent; \
              agent = StoryFinderAgent(); \
              stories = agent.find_stories('AI in healthcare'); \
              print(stories)"
   ```
   Expected: 3-5 relevant story ideas about AI in healthcare
   
3. **Test 2 - Invalid Key**:
   ```bash
   export GEMINI_API_KEY="invalid"
   # Should fail fast with clear error
   ```

4. **Test 3 - Rate Limiting**:
   ```bash
   # Run 20 rapid requests - should queue/delay, not fail
   ```

---

## Files Affected

**Modified:**
- `src/agents/story_finder/agent.py` - Add validation, error handling, logging
- `src/agents/script_writer/agent.py` - Same updates as story_finder
- `src/core/config.py` - Add budget limits, model config
- `requirements.txt` - Add `ratelimit`, callback utilities

**New:**
- `src/core/usage_tracker.py` - Token usage & cost tracking
- `tests/test_story_finder_real.py` - Real API tests
- `tests/test_script_writer_real.py` - Real API tests
- `docs/API_COST_ANALYSIS.md` - Cost estimates and optimization tips

---

## Cost Analysis

### Gemini API Pricing (as of 2024)
- **gemini-1.5-flash**: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **gemini-1.5-pro**: More expensive, higher quality

### Estimated Usage Per Video
- Story generation: ~500 tokens input, ~200 tokens output = ~$0.0001
- Script generation: ~1000 tokens input, ~2000 tokens output = ~$0.0007  
- **Total per video: ~$0.0008** (less than 1 cent)

### Budget Recommendations
- **Development**: 1000 videos/day = $0.80/day = $24/month
- **Production**: 10,000 videos/day = $8/day = $240/month
- **Set daily limit**: $10/day to prevent runaway costs

---

## Success Criteria
- [x] Agent validates API key on startup
- [x] Real LLM generation works end-to-end
- [x] Graceful fallback on API failures
- [x] Token usage logged for all requests
- [x] Rate limiting prevents quota errors
- [x] Integration test passes with real API
- [x] Cost per video < $0.001
- [x] P95 latency < 10 seconds
- [x] Clear error messages for developers

---

## Dependencies
- Depends on: TICKET-007 (consolidated config - DONE ✅)
- Blocks: Production deployment
- Related to: TICKET-011 (cost management), TICKET-013 (monitoring)

---

## References
- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- LangChain Gemini: https://python.langchain.com/docs/integrations/chat/google_generative_ai
- Rate limiting: https://pypi.org/project/ratelimit/
- Cost calculator: https://cloud.google.com/vertex-ai/pricing

---

**Priority: HIGH** - Required for production launch. Cannot deliver core product value without real LLM integration.
