# [TICKET-037] Implement Comprehensive Unit Test Suite for All Agents

## Priority
- [x] Critical (System stability, security, data loss risk)
- [ ] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [x] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [x] Technical Debt
- [ ] Code Duplication

## Impact Assessment

**Business Impact:**
- **Production Reliability**: Current test coverage (~15%) insufficient for production deployment
- **Bug Detection**: Insufficient tests mean bugs reach production
- **Confidence**: Low confidence in making changes without breaking existing functionality
- **Development Speed**: Fear of breaking things slows down development

**Technical Impact:**
- **Modules Affected**: All 7 agents + core modules
- **Files to Change**: ~20 new test files + updates to existing 5 test files
- **Test Count**: From 5 tests to 77+ tests
- **Coverage**: From ~15% to ~80%

**Effort Estimate:**
- Large (5-7 days)

## Problem Description

### Current State

**Location**: `tests/unit/` and `tests/integration/`

**Current Test Coverage** (estimated based on file analysis):

| Module | Test File | Test Count | Coverage | Critical Gaps |
|--------|-----------|------------|----------|---------------|
| story_finder | test_story_finder_v2.py | 2 tests | ~40% | No error handling tests, no search tool tests |
| script_writer | None | 0 tests | 0% | **No tests at all** |
| director | test_director_agent.py | 2 tests | ~30% | No story beat tests, no emotional arc tests |
| image_gen | None | 0 tests | 0% | **No tests at all** |
| voice | None | 0 tests | 0% | **No tests at all** |
| video_gen | test_video_gen_provider.py | 1 test | ~20% | No provider fallback tests |
| video_assembly | None | 0 tests | 0% | **No tests at all** |
| **Total** | **5 files** | **5 tests** | **~15%** | **4 agents completely untested** |

**Existing Tests** (from test_director_agent.py):
```python
class TestDirectorAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = DirectorAgent()
        # Mock LLM
        self.agent.llm = MagicMock()
        self.agent.llm.invoke = MagicMock()

    async def test_analyze_script_structure(self):
        """Test that analyze_script returns a valid DirectedScript structure"""
        # ... basic structure test ...

    async def test_fallback_logic(self):
        """Test fallback when LLM fails"""
        # ... basic fallback test ...
```

**Only 2 tests for Director Agent**, which has:
- 558 lines of code
- 15+ methods
- Complex LLM interactions
- Fallback logic
- Story beat identification
- Emotional arc mapping

### Root Cause Analysis

**Why does this problem exist?**
- **Historical Context**: Tests added reactively when bugs found, not proactively
- **Time Pressure**: Features prioritized over test coverage
- **Complexity**: Async code and LLM mocking perceived as difficult to test
- **Lack of Infrastructure**: No shared test fixtures or utilities

**Pattern that led to this issue:**
1. Agent created to solve immediate need
2. Manual testing deemed "good enough"
3. Integration tests added later
4. Unit tests never prioritized
5. Technical debt accumulated

**Related issues in codebase:**
- No test coverage reporting
- No CI/CD enforcement of coverage thresholds
- Inconsistent test patterns across existing tests

### Evidence

**Test Coverage Gaps** (specific examples):

1. **ScriptWriterAgent** (0 tests):
   - No tests for `_validate_and_fix_script()`
   - No tests for enum value fixing
   - No tests for retry logic
   - No tests for scene count validation

2. **ImageGenAgent** (0 tests):
   - No tests for retry logic with exponential backoff
   - No tests for cache key generation
   - No tests for prompt enhancement
   - No tests for workflow state saving

3. **VoiceAgent** (0 tests):
   - No tests for ElevenLabs integration
   - No tests for tone-based settings
   - No tests for audio file generation

4. **VideoAssemblyAgent** (0 tests):
   - No tests for effect application
   - No tests for audio sync
   - No tests for transition handling

**Production Risks:**
- Regression bugs when refactoring
- Undetected edge cases
- Breaking changes not caught
- Difficult to debug issues

## Proposed Solution

### Approach

**High-level strategy:**
1. Create comprehensive test suite for each agent
2. Establish shared test fixtures and utilities
3. Achieve 80%+ coverage for all critical paths
4. Add edge case and error scenario tests
5. Integrate with CI/CD for automated testing

**Testing Philosophy:**
- **Test Behavior, Not Implementation**: Focus on what agents do, not how
- **Test Edge Cases**: Null inputs, empty lists, invalid data
- **Test Error Paths**: What happens when things fail
- **Test Integration Points**: How agents interact with external services

### Implementation Details

**Step 1: Create Shared Test Infrastructure** (`tests/conftest.py`):

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.models.models import Scene, VideoScript, SceneType, VoiceTone, ImageStyle, VisualSegment

@pytest.fixture
def mock_llm():
    """Mock LLM for all agent tests."""
    llm = MagicMock()
    llm.invoke = AsyncMock()
    return llm

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setattr("src.core.config.settings.USE_REAL_LLM", True)
    monkeypatch.setattr("src.core.config.settings.GEMINI_API_KEY", "test_key")
    monkeypatch.setattr("src.core.config.settings.MIN_SCENES", 4)
    monkeypatch.setattr("src.core.config.settings.MAX_SCENES", 15)

@pytest.fixture
def sample_scene():
    """Sample scene for testing."""
    return Scene(
        scene_number=1,
        scene_type=SceneType.HOOK,
        voice_tone=VoiceTone.EXCITED,
        image_style=ImageStyle.CINEMATIC,
        content=[
            VisualSegment(
                segment_text="Test dialogue",
                image_prompt="Test image prompt"
            )
        ]
    )

@pytest.fixture
def sample_script(sample_scene):
    """Sample script for testing."""
    return VideoScript(
        title="Test Video",
        main_character_description="Test character",
        scenes=[sample_scene] * 4  # Min 4 scenes
    )
```

**Step 2: ScriptWriterAgent Tests** (`tests/unit/test_script_writer_agent.py`):

```python
import pytest
from unittest.mock import MagicMock, patch
from src.agents.script_writer.agent import ScriptWriterAgent
from src.models.models import VideoScript, SceneType, VoiceTone

class TestScriptWriterAgent:
    @pytest.fixture
    def agent(self, mock_settings):
        return ScriptWriterAgent()
    
    def test_initialization_real_mode(self, agent):
        """Test agent initializes correctly in real mode."""
        assert agent.llm is not None
        assert agent.chain is not None
    
    def test_initialization_mock_mode(self, monkeypatch):
        """Test agent initializes correctly in mock mode."""
        monkeypatch.setattr("src.core.config.settings.USE_REAL_LLM", False)
        agent = ScriptWriterAgent()
        assert agent.llm is None
        assert agent.chain is None
    
    def test_initialization_missing_api_key(self, monkeypatch):
        """Test agent raises error when API key missing in real mode."""
        monkeypatch.setattr("src.core.config.settings.USE_REAL_LLM", True)
        monkeypatch.setattr("src.core.config.settings.GEMINI_API_KEY", None)
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
            ScriptWriterAgent()
    
    def test_validate_and_fix_script_valid(self, agent, sample_script):
        """Test validation passes for valid script."""
        result = agent._validate_and_fix_script(sample_script)
        assert result == sample_script
    
    def test_validate_and_fix_script_too_few_scenes(self, agent, sample_scene):
        """Test validation fails for too few scenes."""
        script = VideoScript(
            title="Test",
            main_character_description="Test",
            scenes=[sample_scene]  # Only 1 scene, min is 4
        )
        
        with pytest.raises(ValueError, match="minimum is 4"):
            agent._validate_and_fix_script(script)
    
    def test_validate_and_fix_script_too_many_scenes(self, agent, sample_scene):
        """Test validation truncates scripts with too many scenes."""
        script = VideoScript(
            title="Test",
            main_character_description="Test",
            scenes=[sample_scene] * 20  # 20 scenes, max is 15
        )
        
        result = agent._validate_and_fix_script(script)
        assert len(result.scenes) == 15
    
    def test_validate_and_fix_invalid_voice_tone(self, agent, sample_scene):
        """Test validation fixes invalid voice tone."""
        sample_scene.voice_tone = "explanation"  # Invalid string
        script = VideoScript(
            title="Test",
            main_character_description="Test",
            scenes=[sample_scene] * 4
        )
        
        result = agent._validate_and_fix_script(script)
        assert result.scenes[0].voice_tone == VoiceTone.SERIOUS
    
    @pytest.mark.asyncio
    async def test_generate_script_mock_mode(self, monkeypatch):
        """Test script generation in mock mode."""
        monkeypatch.setattr("src.core.config.settings.USE_REAL_LLM", False)
        agent = ScriptWriterAgent()
        
        result = await agent.generate_script("Test subject")
        
        assert isinstance(result, VideoScript)
        assert len(result.scenes) >= 4
    
    @pytest.mark.asyncio
    async def test_generate_script_with_retry(self, agent, mock_llm):
        """Test script generation retries on validation error."""
        agent.llm = mock_llm
        
        # First attempt fails, second succeeds
        mock_llm.invoke.side_effect = [
            ValidationError("Invalid"),
            valid_script_response
        ]
        
        result = await agent.generate_script("Test subject")
        
        assert mock_llm.invoke.call_count == 2
        assert isinstance(result, VideoScript)
    
    @pytest.mark.asyncio
    async def test_generate_script_max_retries_exhausted(self, agent, mock_llm):
        """Test script generation fails after max retries."""
        agent.llm = mock_llm
        mock_llm.invoke.side_effect = ValidationError("Invalid")
        
        with pytest.raises(ValidationError):
            await agent.generate_script("Test subject", max_retries=3)
        
        assert mock_llm.invoke.call_count == 3
```

**Step 3: ImageGenAgent Tests** (`tests/unit/test_image_gen_agent.py`):

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.agents.image_gen.agent import ImageGenAgent

class TestImageGenAgent:
    @pytest.fixture
    def agent(self):
        return ImageGenAgent()
    
    def test_initialization(self, agent):
        """Test agent initializes with correct directories."""
        assert agent.output_dir.endswith("images")
        assert agent.cache_dir.endswith("cache")
    
    def test_cache_key_generation(self, agent):
        """Test cache key is deterministic."""
        key1 = agent._cache_key("test prompt", "model1")
        key2 = agent._cache_key("test prompt", "model1")
        key3 = agent._cache_key("different prompt", "model1")
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key
    
    def test_enhance_prompt_text(self, agent):
        """Test prompt enhancement adds quality modifiers."""
        from src.models.models import ImageStyle
        
        enhanced = agent._enhance_prompt_text("A cat", ImageStyle.CINEMATIC)
        
        assert "A cat" in enhanced
        assert "photorealistic" in enhanced
        assert "cinematic" in enhanced
    
    @pytest.mark.asyncio
    async def test_generate_images_mock_mode(self, agent, sample_scene):
        """Test image generation in mock mode."""
        agent.mock_mode = True
        
        result = await agent.generate_images([sample_scene])
        
        assert 1 in result
        assert len(result[1]) > 0
        assert result[1][0].endswith(".png")
    
    @pytest.mark.asyncio
    async def test_generate_images_with_retry(self, agent, sample_scene, monkeypatch):
        """Test image generation retries on failure."""
        agent.mock_mode = False
        
        mock_client = MagicMock()
        mock_client.generate_image = AsyncMock()
        
        # First attempt fails, second succeeds
        mock_client.generate_image.side_effect = [
            Exception("API Error"),
            "https://example.com/image.png"
        ]
        
        with patch('src.agents.image_gen.agent.GeminiImageClient', return_value=mock_client):
            result = await agent.generate_images([sample_scene])
        
        assert mock_client.generate_image.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_images_max_retries_exhausted(self, agent, sample_scene):
        """Test image generation fails after max retries."""
        agent.mock_mode = False
        
        mock_client = MagicMock()
        mock_client.generate_image = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('src.agents.image_gen.agent.GeminiImageClient', return_value=mock_client):
            with pytest.raises(RuntimeError, match="failed for scene"):
                await agent.generate_images([sample_scene])
```

**Step 4: Similar test suites for**:
- DirectorAgent (expand existing 2 tests to 15+ tests)
- VoiceAgent (8+ tests)
- VideoGenAgent (10+ tests)
- VideoAssemblyAgent (12+ tests)
- StoryFinderAgent (expand existing 2 tests to 10+ tests)

### Alternative Approaches Considered

**Option 1: Integration Tests Only**
- Focus on end-to-end tests instead of unit tests
- **Why not chosen**: Integration tests are slower, harder to debug, don't catch unit-level issues

**Option 2: Property-Based Testing**
- Use hypothesis for property-based testing
- **Why not chosen**: Adds complexity, team not familiar with approach

**Option 3: Snapshot Testing**
- Use snapshot tests for LLM outputs
- **Why not chosen**: LLM outputs are non-deterministic

### Benefits

- **Improved reliability**: Catch bugs before production
- **Better maintainability**: Refactor with confidence
- **Enhanced testability**: Easier to test new features
- **Faster debugging**: Pinpoint issues quickly
- **Documentation**: Tests serve as usage examples

### Risks & Considerations

- **Time Investment**: 5-7 days of focused work
- **Learning Curve**: Team needs to learn async testing patterns
- **Maintenance**: Tests need to be maintained alongside code
- **False Positives**: Flaky tests can reduce confidence

**Mitigation:**
- Invest in shared test infrastructure
- Document testing patterns
- Use stable mocking strategies
- Regular test maintenance

## Testing Strategy

### Test Categories

1. **Initialization Tests**: Verify agents initialize correctly
2. **Happy Path Tests**: Test normal operation
3. **Error Handling Tests**: Test failure scenarios
4. **Edge Case Tests**: Test boundary conditions
5. **Integration Tests**: Test agent interactions

### Coverage Goals

| Module | Target Coverage | Test Count |
|--------|----------------|------------|
| story_finder | 80%+ | 10+ tests |
| script_writer | 80%+ | 10+ tests |
| director | 85%+ | 15+ tests |
| image_gen | 80%+ | 12+ tests |
| voice | 80%+ | 8+ tests |
| video_gen | 80%+ | 10+ tests |
| video_assembly | 80%+ | 12+ tests |
| **Total** | **~80%** | **77+ tests** |

## Files Affected

### New Test Files
- `tests/conftest.py` - Shared fixtures (if doesn't exist)
- `tests/unit/test_script_writer_agent.py` - ScriptWriter tests
- `tests/unit/test_image_gen_agent.py` - ImageGen tests
- `tests/unit/test_voice_agent.py` - Voice tests
- `tests/unit/test_video_assembly_agent.py` - VideoAssembly tests

### Modified Test Files
- `tests/unit/test_director_agent.py` - Expand from 2 to 15+ tests
- `tests/unit/test_story_finder_v2.py` - Expand from 2 to 10+ tests
- `tests/unit/test_video_gen_provider.py` - Expand from 1 to 10+ tests

### Configuration Files
- `pytest.ini` or `pyproject.toml` - Add coverage configuration
- `.github/workflows/test.yml` - Add CI/CD test automation (if exists)

## Dependencies

- **Depends on**: TICKET-036 (Base Class - makes testing easier)
- **Blocks**: None (but improves confidence for all future work)
- **Related to**: TICKET-043 (Integration Tests)

## References

- **Related documentation**: `docs/agents/README.md`
- **Testing frameworks**: pytest, pytest-asyncio, pytest-cov
- **Mocking libraries**: unittest.mock

## Architect Review Questions

**For the architect to consider:**
1. Is 80% coverage sufficient, or should we aim higher?
2. Should we enforce coverage thresholds in CI/CD?
3. What's the priority order for testing agents?
4. Should we use pytest or unittest framework?
5. Any specific testing patterns or standards to follow?

## Success Criteria

- [ ] All 7 agents have comprehensive unit tests
- [ ] Test coverage reaches 80%+ for all agents
- [ ] Shared test fixtures created and documented
- [ ] All tests pass consistently
- [ ] CI/CD integration (if applicable)
- [ ] Test documentation added to README
- [ ] Code review approved

---

**Estimated Effort**: 5-7 days  
**Priority**: Critical  
**Risk**: Low (additive only, no functional changes)  
**ROI**: Very High (60% reduction in production bugs)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **Production Readiness**: We cannot deploy confidently without this. 15% coverage is a major risk.
- **Refactoring Safety**: We are planning major refactors (Base Class, Async, Error Handling). These tests are the safety net that allows us to move fast without breaking things.
- **Documentation**: Tests are the best documentation for how agents are *supposed* to behave.

**Implementation Phase:** Phase 1 - Foundation & Quality
**Sequence Order:** #3 in implementation queue (Parallel with or immediately after TICKET-036)

**Architectural Guidance:**
Key considerations for implementation:
- **Framework**: Use `pytest` exclusively. It's more pythonic and powerful than `unittest`.
- **Mocking**: Be careful not to over-mock. Mock external IO (LLM calls, APIs), but test the internal logic (validation, parsing, state updates) with real objects where possible.
- **Fixtures**: `tests/conftest.py` is the right place for shared fixtures. Keep them clean and reusable.
- **Coverage**: 80% is a good target. 100% is often diminishing returns. Focus on *critical paths* and *error handling*.

**Dependencies:**
- **Must complete first**: TICKET-036 (Base Class) - It's much better to write tests against the new `BaseAgent` structure than to write them for the old structure and rewrite them immediately.
- **Should complete first**: None
- **Blocks**: TICKET-043 (Integration Tests)

**Risk Mitigation:**
- **Test Maintenance**: Ensure tests are not brittle. Avoid testing private methods unless absolutely necessary. Test the public interface.
- **Performance**: Keep unit tests fast. Mock all network calls.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] `pytest` configuration added to `pyproject.toml` or `pytest.ini`.
- [ ] Tests run in < 10 seconds total (mocked).
- [ ] CI pipeline fails if tests fail.

**Alternative Approaches Considered:**
- **Selected approach:** Comprehensive Unit Tests with `pytest` and shared fixtures.

**Implementation Notes:**
- Start by creating `tests/conftest.py` with the `mock_llm` and `mock_settings` fixtures.
- Then implement tests for `BaseAgent` (from TICKET-036).
- Then proceed agent by agent.

**Estimated Timeline**: 5-7 days
**Recommended Owner**: QA Engineer / Senior Backend Engineer
