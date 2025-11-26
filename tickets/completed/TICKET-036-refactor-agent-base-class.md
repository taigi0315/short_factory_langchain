# [TICKET-036] Refactor Agent Base Class to Eliminate Initialization Duplication

## Priority
- [x] Critical (System stability, security, data loss risk)
- [ ] High (Performance issues, significant tech debt)
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
- **Maintenance Burden**: Currently, any change to agent initialization must be made in 7 places
- **Inconsistency Risk**: Agents may behave differently due to copy-paste errors
- **Development Speed**: New agents require ~50 lines of boilerplate code
- **Bug Surface Area**: Duplicated code increases likelihood of bugs

**Technical Impact:**
- **Modules Affected**: All 7 agents (story_finder, script_writer, director, image_gen, voice, video_gen, video_assembly)
- **Files to Change**: ~10 files (7 agent files + 1 new base class + 2 test files)
- **Breaking Changes**: Minimal (internal refactoring only)
- **Code Reduction**: ~200 lines of duplicated code eliminated

**Effort Estimate:**
- Medium (2-3 days)

## Problem Description

### Current State

**Location**: All agent `__init__` methods across:
- `src/agents/story_finder/agent.py:22-67`
- `src/agents/script_writer/agent.py:48-75`
- `src/agents/director/agent.py:60-67`
- `src/agents/image_gen/agent.py:18-27`
- `src/agents/voice/agent.py:15-40`
- `src/agents/video_gen/agent.py:20-45`
- `src/agents/video_assembly/agent.py:15-30`

**Current Problematic Code** (from story_finder/agent.py):
```python
class StoryFinderAgent:
    def __init__(self):
        """
        Initialize StoryFinderAgent with API validation.
        Raises ValueError if API key is missing in real mode.
        """
        # Validate API key if using real LLM
        if settings.USE_REAL_LLM:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required when USE_REAL_LLM=true. "
                    "Please set it in your .env file or environment variables."
                )
            logger.info("✅ StoryFinderAgent initializing with REAL Gemini LLM")
            
            # Initialize LLM with error handling and retries
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_retries=3,  # Retry failed requests
                request_timeout=30.0,  # 30 second timeout
            )
            
            # ... agent-specific setup ...
            
        else:
            logger.info("⚠️ StoryFinderAgent in MOCK mode (USE_REAL_LLM=false)")
            self.llm = None
            self.chain = None
```

**This pattern is duplicated 7 times** with only minor variations (agent name, temperature, specific setup).

### Root Cause Analysis

**Why does this problem exist?**
- **Historical Context**: Agents were created independently without a base class
- **Copy-Paste Development**: Each new agent copied initialization from existing agents
- **No Refactoring**: As the pattern evolved, changes weren't backported to all agents
- **Lack of Abstraction**: No shared base class was created to encapsulate common behavior

**Pattern that led to this issue:**
1. First agent (story_finder) created with full initialization
2. Subsequent agents copied the pattern
3. Minor improvements made to individual agents
4. Divergence increased over time

**Related issues in codebase:**
- Similar duplication in error handling (see TICKET-039)
- Similar duplication in retry logic (see TICKET-039)
- Inconsistent logging patterns

### Evidence

**Code Duplication Metrics:**
- **Lines duplicated**: ~45 lines per agent × 7 agents = ~315 lines
- **Actual unique logic**: ~100 lines (after deduplication)
- **Duplication ratio**: 68% of initialization code is duplicated
- **Maintenance cost**: 7x effort for any initialization change

**Specific Duplicated Patterns:**
1. API key validation (7 occurrences)
2. LLM initialization (7 occurrences)
3. Mock mode handling (7 occurrences)
4. Logging statements (14+ occurrences)

**Test Coverage Impact:**
- Each agent needs identical setup tests
- Currently only 2/7 agents have initialization tests
- Test duplication: ~30 lines per agent test

## Proposed Solution

### Approach

**High-level strategy:**
1. Create `BaseAgent` abstract class with common initialization logic
2. Extract LLM initialization to shared method
3. Provide hooks for agent-specific setup
4. Migrate all agents to inherit from `BaseAgent`
5. Update tests to use shared test fixtures

**Design pattern to apply:**
- **Template Method Pattern**: Base class defines initialization skeleton, subclasses override specific steps
- **Dependency Injection**: LLM and configuration injected via base class

### Implementation Details

**Step 1: Create BaseAgent** (`src/agents/base_agent.py`):

```python
from abc import ABC, abstractmethod
from typing import Optional
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

logger = structlog.get_logger()

class BaseAgent(ABC):
    """
    Base class for all AI agents in the ShortFactory pipeline.
    
    Provides common initialization logic including:
    - API key validation
    - LLM initialization
    - Mock mode handling
    - Logging setup
    """
    
    def __init__(
        self,
        agent_name: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        request_timeout: float = 30.0,
        require_llm: bool = True
    ):
        """
        Initialize base agent with common setup.
        
        Args:
            agent_name: Name of the agent (for logging)
            temperature: LLM temperature setting
            max_retries: Number of retry attempts for LLM calls
            request_timeout: Timeout for LLM requests in seconds
            require_llm: Whether this agent requires LLM (False for image/video agents)
        """
        self.agent_name = agent_name
        self.mock_mode = not settings.USE_REAL_LLM
        self.llm: Optional[ChatGoogleGenerativeAI] = None
        
        if require_llm:
            self._initialize_llm(temperature, max_retries, request_timeout)
        
        # Call agent-specific setup
        self._setup()
        
        logger.info(
            f"{agent_name} initialized",
            mode="REAL" if not self.mock_mode else "MOCK"
        )
    
    def _initialize_llm(
        self,
        temperature: float,
        max_retries: int,
        request_timeout: float
    ):
        """Initialize LLM with validation and error handling."""
        if not self.mock_mode:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    f"GEMINI_API_KEY is required for {self.agent_name} when USE_REAL_LLM=true. "
                    "Please set it in your .env file or environment variables."
                )
            
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature,
                max_retries=max_retries,
                request_timeout=request_timeout,
                # Add explicit error handling/retry config if supported by library
            )
            
            logger.info(
                f"✅ {self.agent_name} initializing with REAL Gemini LLM",
                model=settings.llm_model_name
            )
        else:
            logger.info(f"⚠️ {self.agent_name} in MOCK mode (USE_REAL_LLM=false)")
    
    @abstractmethod
    def _setup(self):
        """
        Agent-specific setup logic.
        Override this method to add custom initialization.
        """
        pass
```

**Step 2: Refactor StoryFinderAgent** (example):

```python
from src.agents.base_agent import BaseAgent

class StoryFinderAgent(BaseAgent):
    def __init__(self):
        # Call base class with agent-specific parameters
        super().__init__(
            agent_name="StoryFinderAgent",
            temperature=0.7,
            max_retries=3,
            request_timeout=30.0
        )
    
    def _setup(self):
        """Agent-specific setup."""
        # Initialize Search Tool (Tavily)
        self.search_tool = None
        if not self.mock_mode and settings.TAVILY_API_KEY:
            try:
                self.search_tool = TavilySearchResults(
                    tavily_api_key=settings.TAVILY_API_KEY,
                    max_results=3
                )
                logger.info("✅ Tavily Search Tool initialized")
            except Exception as e:
                logger.error(f"⚠️ Failed to initialize Tavily: {e}")
                self.search_tool = None
        
        # Build the dynamic chain
        if not self.mock_mode:
            self.chain = self._build_chain()
        else:
            self.chain = None
```

**Step 3: Update Other Agents** (similar pattern for all 7 agents)

**Step 4: Create Shared Test Fixtures** (`tests/conftest.py`):

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_llm():
    """Shared fixture for mocking LLM across all agent tests."""
    llm = MagicMock()
    llm.invoke = MagicMock()
    return llm

@pytest.fixture
def mock_settings(monkeypatch):
    """Shared fixture for mocking settings."""
    monkeypatch.setattr("src.core.config.settings.USE_REAL_LLM", True)
    monkeypatch.setattr("src.core.config.settings.GEMINI_API_KEY", "test_key")
    return settings
```

### Alternative Approaches Considered

**Option 1: Composition over Inheritance**
- Create `AgentInitializer` helper class
- Each agent uses composition: `self.initializer = AgentInitializer()`
- **Why not chosen**: More verbose, doesn't leverage OOP benefits

**Option 2: Factory Pattern**
- Create `AgentFactory.create_agent(type, config)`
- **Why not chosen**: Doesn't reduce duplication in agent classes themselves

**Option 3: Mixin Classes**
- Create `LLMInitMixin`, `MockModeMixin`, etc.
- **Why not chosen**: Multiple inheritance complexity, harder to understand

### Benefits

- **Improved maintainability**: Changes to initialization logic made in one place
- **Reduced complexity**: Each agent ~40 lines shorter
- **Better testability**: Shared test fixtures reduce test duplication
- **Enhanced consistency**: All agents behave identically for common operations
- **Easier onboarding**: New developers see clear inheritance hierarchy
- **Faster development**: New agents require minimal boilerplate

### Risks & Considerations

- **Breaking changes**: Agents must be refactored to use base class
- **Migration effort**: All 7 agents must be updated simultaneously
- **Testing burden**: All agent tests must be updated
- **Backward compatibility**: Ensure existing functionality unchanged

**Mitigation:**
- Implement incrementally (one agent at a time)
- Extensive testing before and after refactoring
- Keep old code commented during transition
- Feature flag for rollback if needed

## Testing Strategy

### Unit Tests to Add

1. **BaseAgent Tests** (`tests/unit/test_base_agent.py`):
   - Test LLM initialization in real mode
   - Test mock mode handling
   - Test API key validation
   - Test error handling for missing keys
   - Test agent-specific setup hook

2. **Agent Migration Tests**:
   - Verify each agent still works after refactoring
   - Test that agent-specific logic unchanged
   - Test mock mode still works

3. **Integration Tests**:
   - Test complete workflow with refactored agents
   - Verify no regression in functionality

### Test Coverage Goals

- BaseAgent: 100% coverage
- Each agent __init__: 90%+ coverage
- Integration tests: All critical workflows

## Files Affected

### New Files
- `src/agents/base_agent.py` - New base class
- `tests/unit/test_base_agent.py` - Base class tests
- `tests/conftest.py` - Shared test fixtures (if doesn't exist)

### Modified Files
- `src/agents/story_finder/agent.py` - Inherit from BaseAgent
- `src/agents/script_writer/agent.py` - Inherit from BaseAgent
- `src/agents/director/agent.py` - Inherit from BaseAgent
- `src/agents/image_gen/agent.py` - Inherit from BaseAgent (adapt for non-LLM)
- `src/agents/voice/agent.py` - Inherit from BaseAgent (adapt for non-LLM)
- `src/agents/video_gen/agent.py` - Inherit from BaseAgent (adapt for non-LLM)
- `src/agents/video_assembly/agent.py` - Inherit from BaseAgent (adapt for non-LLM)
- `tests/unit/test_story_finder_v2.py` - Use shared fixtures
- `tests/unit/test_director_agent.py` - Use shared fixtures

## Dependencies

- **Depends on**: None
- **Blocks**: TICKET-037 (Unit Tests - easier with base class)
- **Blocks**: TICKET-039 (Error Handling - can be added to base class)
- **Related to**: TICKET-041 (Configuration - base class uses settings)

## References

- **Related documentation**: `docs/agents/README.md`
- **Design patterns**: Template Method Pattern, Dependency Injection
- **Similar issues**: None (this is the foundational refactoring)

## Architect Review Questions

**For the architect to consider:**
1. Should we use inheritance (BaseAgent) or composition (AgentInitializer helper)?
2. Should non-LLM agents (image, voice, video) also inherit from BaseAgent?
3. What's the migration strategy - all at once or incremental?
4. Should we add additional common methods to BaseAgent (e.g., retry logic)?
5. Is there a better name than `BaseAgent` (e.g., `Agent`, `AbstractAgent`, `AgentBase`)?

## Success Criteria

- [ ] BaseAgent class created and tested (100% coverage)
- [ ] All 7 agents refactored to use BaseAgent
- [ ] Code duplication reduced by 200+ lines
- [ ] All existing tests pass
- [ ] New shared test fixtures created
- [ ] No regression in functionality
- [ ] Documentation updated
- [ ] Code review approved

---

**Estimated Effort**: 2-3 days  
**Priority**: Critical  
**Risk**: Medium  
**ROI**: High (40% reduction in agent code, easier maintenance)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **Foundational Stability**: Centralizing agent initialization is crucial for enforcing consistent behavior (logging, error handling, config) across the system.
- **Scalability**: As we add more agents or capabilities (like observability or new LLM providers), we only need to update the `BaseAgent`.
- **Code Health**: Eliminating ~200 lines of copy-pasted code significantly reduces technical debt and maintenance overhead.

**Implementation Phase:** Phase 1 - Foundation & Quality
**Sequence Order:** #1 in implementation queue

**Architectural Guidance:**
Key considerations for implementation:
- **Inheritance vs Composition**: Inheritance (`BaseAgent`) is appropriate here as "is-a" relationship holds strong (StoryFinder *is an* Agent). It simplifies the mental model for agent developers.
- **Non-LLM Agents**: Yes, they should inherit from `BaseAgent`. The `require_llm` flag in `__init__` is a good design choice to handle this variation while keeping a unified hierarchy.
- **Migration Strategy**: Do it incrementally. Create `BaseAgent` first, then migrate one agent (e.g., `StoryFinder`) and verify, then proceed to others.
- **Naming**: `BaseAgent` is standard and clear. `AbstractAgent` is also fine, but `BaseAgent` implies it contains shared implementation, which it does.

**Dependencies:**
- **Must complete first**: None
- **Should complete first**: TICKET-041 (Extract Hardcoded Config) - ideally, `BaseAgent` should use the new settings structure immediately.
- **Blocks**: TICKET-037, TICKET-039

**Risk Mitigation:**
- **Regression**: Run existing integration tests after each agent migration.
- **Complexity**: Keep `BaseAgent` lightweight. Don't dump *everything* there. Only truly common logic (init, logging, basic config).

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] `BaseAgent` uses `TICKET-041` settings if available.
- [ ] `BaseAgent` is documented in `docs/agents/README.md` as the standard for new agents.
- [ ] All 7 agents successfully inherit and pass their individual unit tests (once created).

**Alternative Approaches Considered:**
- **Selected approach:** Inheritance (`BaseAgent`) because it enforces a contract and standardizes the lifecycle (`__init__` -> `_setup`) which is critical for a pipeline of agents.

**Implementation Notes:**
- Start by creating `src/agents/base_agent.py`.
- Ensure `structlog` is set up correctly in the base.
- When migrating `ImageGenAgent` and others, ensure `require_llm=False` is passed correctly.

**Estimated Timeline**: 2-3 days
**Recommended Owner**: Senior Backend Engineer
