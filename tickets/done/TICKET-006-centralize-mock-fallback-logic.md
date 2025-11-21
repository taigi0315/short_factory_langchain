# [TICKET-006] Centralize Duplicate Mock Fallback Logic Across API Routes

## Priority
- [ ] Critical (System stability, security, data loss risk)
- [ ] High (Performance issues, significant tech debt)
- [x] Medium (Code quality, maintainability improvements)
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
- **MEDIUM**: No immediate user impact, but affects maintainability
- Mock data is currently inconsistent across endpoints
- Adding new endpoints requires duplicating the same fallback pattern
- Risk of mock data getting out of sync (already happened - old fields referenced)

**Technical Impact:**
- Affects: All API routes (`stories.py`, `scripts.py`, `videos.py`)
- Files needing changes: 3 route files + 1 new utility file
- **Code duplication**: ~40 lines of try/catch/mock pattern repeated 3 times
- Current pattern is error-prone and violates DRY principle

**Effort Estimate:**
- Small (< 1 day) - 3-4 hours

## Problem Description

### Current State
**Locations:** 
- `src/api/routes/stories.py:32-51` (20 lines of mock fallback)
- `src/api/routes/scripts.py:29-75` (47 lines of mock fallback)
- `src/api/routes/videos.py:23-24` (minimal error handling, no mock)

Every API endpoint follows the same pattern:
```python
@router.post("/generate")
async def some_endpoint(request: SomeRequest):
    try:
        # Real implementation
        agent = SomeAgent()
        result = agent.do_something()
        return Response(data=result)
    except Exception as e:
        print(f"Error: {e}")  # ❌ print() instead of logging
        # ❌ Duplicate mock data definition
        return Response(data=HARDCODED_MOCK_DATA)
```

**Problems:**
1. **Code duplication**: Try/catch/fallback pattern repeated in every route
2. **Inconsistent error handling**: 
   - `stories.py` and `scripts.py` swallow all exceptions and return mock data
   - `videos.py` raises HTTPException (inconsistent!)
3. **No logging**: Uses `print()` instead of proper logging framework
4. **No error visibility**: Users get successful 200 response even when LLM fails
5. **Mock data maintenance**: Mock data is embedded in routes, hard to update
6. **Error details lost**: `except Exception` catches everything, losing valuable debugging info

### Root Cause Analysis
The duplicate pattern emerged during rapid prototype development where each route was implemented independently. The "verification platform" requirement (UI should work without API keys) led to adding mock fallbacks, but they were copy-pasted rather than centralized.

This is classic technical debt from prototyping without refactoring.

### Evidence

**Duplication Example** - Same pattern 3 times:
```python
# stories.py lines 32-51
except Exception as e:
    print(f"Error generating stories: {e}")
    return [StoryIdeaResponse(...), StoryIdeaResponse(...)]

# scripts.py lines 29-75  
except Exception as e:
    print(f"Error generating script: {e}")
    from src.models.models import ElevenLabsSettings
    mock_scenes = [Scene(...), Scene(...)]
    return ScriptGenerationResponse(script=VideoScript(...))

# videos.py lines 23-24
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Different pattern!
```

**Code Duplication Metrics:**
- Mock fallback logic: ~87 lines total across 3 files
- Try/catch wrapper: 3 identical instances
- Total duplication: ~100 lines that should be ~20 lines + data files

## Proposed Solution

### Approach
Create a centralized error handling and mock data system:

1. **Error handling decorator/utility** for consistent try/catch behavior
2. **Mock data repository** separate from business logic
3. **Structured logging** instead of print statements
4. **Conditional mock mode** via environment variable

### Implementation Details

**Step 1: Create mock data repository**
```python
# src/api/mock_data.py
"""
Centralized mock/fallback data for verification platform.
Used when LLM APIs are unavailable or keys are missing.
"""
from src.api.schemas.stories import StoryIdeaResponse
from src.api.schemas.scripts import ScriptGenerationResponse
from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, TransitionType, HookTechnique, ElevenLabsSettings


def get_mock_stories() -> list[StoryIdeaResponse]:
    """Returns mock story ideas for testing/demo."""
    return [
        StoryIdeaResponse(
            title="Mock Story 1: The Coffee Cat",
            premise="A cat that only drinks premium espresso.",
            genre="Comedy",
            target_audience="Cat Lovers",
            estimated_duration="30s"
        ),
        StoryIdeaResponse(
            title="Mock Story 2: Bean's Journey",
            premise="The life cycle of a coffee bean told as an epic saga.",
            genre="Documentary",
            target_audience="Coffee Nerds",
            estimated_duration="60s"
        )
    ]


def get_mock_script(title: str) -> ScriptGenerationResponse:
    """Returns mock video script for testing/demo."""
    mock_scenes = [
        Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            dialogue="You think I drink this swill? I am a connoisseur!",
            voice_tone=VoiceTone.SARCASTIC,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.SARCASTIC),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt="Close up, fluffy cat, disgusted face, cheap coffee cup",
            character_pose="looking disgusted",
            background_description="Coffee shop table",
            needs_animation=True,
            video_prompt="Cat looks at coffee with disgust",
            transition_to_next=TransitionType.ZOOM_IN,
            hook_technique=HookTechnique.VISUAL_SURPRISE
        ),
        Scene(
            scene_number=2,
            scene_type=SceneType.STORY_TELLING,
            dialogue="Only the finest beans for this whiskers.",
            voice_tone=VoiceTone.CONFIDENT,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt="Cat paw knocking cup, slow motion",
            character_pose="swiping paw",
            background_description="Coffee shop table",
            needs_animation=True,
            video_prompt="Cat paw knocks cup off table",
            transition_to_next=TransitionType.FADE,
            hook_technique=None
        )
    ]
    
    return ScriptGenerationResponse(
        script=VideoScript(
            title=title,
            main_character_description="A snobby but adorable cat.",
            overall_style="Comedy",
            scenes=mock_scenes
        )
    )
```

**Step 2: Create error handling utility**
```python
# src/api/error_handling.py
"""
Centralized error handling for API routes.
Provides consistent logging, monitoring, and fallback behavior.
"""
import logging
from functools import wraps
from typing import Callable, TypeVar, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

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
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={"args": args, "kwargs": kwargs}
                )
                
                # Return mock data for verification platform
                logger.warning(f"Falling back to mock data for {func.__name__}")
                return mock_data_fn(*args, **kwargs)
        
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
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return wrapper
```

**Step 3: Refactor routes to use new utilities**
```python
# src/api/routes/stories.py - AFTER refactoring
from fastapi import APIRouter
from src.api.schemas.stories import StoryGenerationRequest, StoryIdeaResponse
from src.agents.story_finder.agent import StoryFinderAgent
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_stories
from typing import List

router = APIRouter()


@router.post("/generate", response_model=List[StoryIdeaResponse])
@with_fallback(lambda req: get_mock_stories())
async def generate_stories(request: StoryGenerationRequest):
    """Generate story ideas using LLM."""
    agent = StoryFinderAgent()
    enhanced_subject = f"{request.topic} (Mood: {request.mood}, Category: {request.category})"
    story_list = agent.find_stories(enhanced_subject)
    
    return [
        StoryIdeaResponse(
            title=story.title,
            premise=story.premise,
            genre=story.genre,
            target_audience=story.target_audience,
            estimated_duration=story.estimated_duration
        ) for story in story_list.stories
    ]
```

**Before/After Comparison:**
```
BEFORE: 52 lines (stories.py)
AFTER: 22 lines (stories.py) + shared utilities

BEFORE: 76 lines (scripts.py)
AFTER: 18 lines (scripts.py) + shared utilities

BEFORE: 25 lines (videos.py)
AFTER: 15 lines (videos.py) + shared utilities

Total: 153 lines → 55 lines + 80 lines of reusable utilities
Reduction: 18 lines saved immediately, scales with each new endpoint
```

### Alternative Approaches Considered
**Option 1**: Use FastAPI exception handlers at app level
- **Why not chosen**: Doesn't solve mock data duplication, only error responses

**Option 2**: Create base route class with common behavior
- **Why not chosen**: Decorators are more Pythonic and composable

**Option 3**: Feature flag system for mock vs real mode
- **Considered for future**: Good idea, but adds complexity. Can build on top of this refactoring later.

### Benefits
- ✅ **50% less code** in route files (easier to read and maintain)
- ✅ **Consistent error handling** across all endpoints
- ✅ **Better observability**: Structured logging instead of print()
- ✅ **Single source of truth** for mock data (easier to update)
- ✅ **Testable**: Mock data can be independently tested
- ✅ **Extensible**: Easy to add new endpoints with same pattern

### Risks & Considerations
- Requires refactoring all existing routes (low risk, mechanical change)
- Need to add Python logging configuration in main.py
- Mock data file grows as features are added (manageable, good documentation)
- Backwards compatible: No API contract changes

## Testing Strategy
**Unit tests:**
```python
# tests/test_error_handling.py
def test_with_fallback_success():
    """Test decorator allows successful execution."""
    @with_fallback(lambda: "mock")
    async def test_fn():
        return "real"
    
    assert await test_fn() == "real"


def test_with_fallback_on_error():
    """Test decorator returns mock data on exception."""
    @with_fallback(lambda: "mock")
    async def test_fn():
        raise ValueError("test error")
    
    assert await test_fn() == "mock"


# tests/test_mock_data.py
def test_mock_stories_valid():
    """Test mock stories match schema."""
    stories = get_mock_stories()
    assert len(stories) > 0
    for story in stories:
        assert isinstance(story, StoryIdeaResponse)
```

**Integration tests:**
- Test each endpoint works with decorator
- Test fallback activates on error
- Test logging output is captured

## Files Affected
**New files:**
- `src/api/error_handling.py` (~60 lines) - Centralized error handling
- `src/api/mock_data.py` (~80 lines) - Mock data repository
- `tests/test_error_handling.py` (~40 lines) - Tests for utilities
- `tests/test_mock_data.py` (~30 lines) - Tests for mock data

**Modified files:**
- `src/api/routes/stories.py` - Refactor to use decorator (52 → 22 lines)
- `src/api/routes/scripts.py` - Refactor to use decorator (76 → 18 lines)
- `src/api/routes/videos.py` - Add consistent error handling (25 → 15 lines)
- `src/api/main.py` - Add logging configuration

**Net change:** +210 new lines, -105 duplicate lines = +105 lines (but much better organized)

## Dependencies
- Depends on: None (can be done anytime)
- Blocks: None
- Related to: All API routes
- Enables: Easier addition of new endpoints with consistent patterns

## References
- FastAPI error handling: https://fastapi.tiangolo.com/tutorial/handling-errors/
- Python logging best practices: https://docs.python.org/3/howto/logging.html
- DRY principle: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself

## Architect Review Questions
1. Should mock fallback be environment-configurable (e.g. disable in production)?
2. Do we want different logging levels for different error types?
3. Should we add monitoring/metrics hooks in the error handler?
4. Do we want to return a 200 OK with mock data, or a 503 Service Unavailable with mock data in the body?
5. Should mock data be loaded from JSON files instead of Python code?

## Success Criteria
- [x] All duplicate try/catch logic removed from route files
- [x] Mock data centralized in single file
- [x] Uses Python logging instead of print()
- [x] All routes use consistent error handling pattern
- [x] No API contract changes (backwards compatible)
- [x] Tests pass for all refactored routes
- [x] Code reduction: > 40 lines saved across route files
- [x] Extensibility: New routes can use decorator in 1 line

---

**Refactoring Impact**: This is a classic "pay now or pay later" situation. Every new endpoint we add without this refactoring multiplies the technical debt. Doing it now pays dividends on all future development.
