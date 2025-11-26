# [TICKET-041] Extract Hardcoded Configuration Values to Settings

## Priority
- [ ] Critical
- [ ] High
- [x] Medium
- [ ] Low

## Type
- [x] Refactoring
- [x] Technical Debt

## Impact Assessment

**Business Impact**: Easier configuration management, no code changes for config updates

**Technical Impact**:
- Modules Affected: All agents
- Files to Change: ~15 files
- Configuration Values: ~15 hardcoded values to extract
- Breaking Changes: None

**Effort Estimate**: Small (1-2 days)

## Problem Description

### Current State

Configuration values hardcoded throughout codebase:

**Example 1** (retry counts):
```python
max_retries = 3  # Hardcoded in multiple places
```

**Example 2** (timeouts):
```python
request_timeout=30.0  # Hardcoded
```

**Example 3** (temperature):
```python
temperature=0.7  # Hardcoded
```

**Example 4** (image dimensions):
```python
if settings.IMAGE_ASPECT_RATIO == "9:16":
    width, height = 1080, 1920  # Hardcoded dimensions
```

### Hardcoded Values Found

| Value | Location | Should Be |
|-------|----------|-----------|
| `max_retries=3` | Multiple agents | `settings.DEFAULT_MAX_RETRIES` |
| `temperature=0.7` | Multiple agents | `settings.DEFAULT_LLM_TEMPERATURE` |
| `request_timeout=30.0` | Multiple agents | `settings.DEFAULT_REQUEST_TIMEOUT` |
| `width=1080, height=1920` | image_gen | `settings.IMAGE_WIDTH_9_16`, `settings.IMAGE_HEIGHT_9_16` |
| `max_results=3` | story_finder | `settings.SEARCH_MAX_RESULTS` |

## Proposed Solution

### Implementation

**Step 1: Add Settings** (`src/core/config.py`):

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LLM Configuration
    DEFAULT_LLM_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    DEFAULT_REQUEST_TIMEOUT: float = Field(default=30.0, ge=5.0, le=300.0)
    
    # Image Dimensions
    IMAGE_WIDTH_9_16: int = Field(default=1080)
    IMAGE_HEIGHT_9_16: int = Field(default=1920)
    IMAGE_WIDTH_16_9: int = Field(default=1920)
    IMAGE_HEIGHT_16_9: int = Field(default=1080)
    
    # Search Configuration
    SEARCH_MAX_RESULTS: int = Field(default=3, ge=1, le=10)
```

**Step 2: Update Agents**:

```python
# Before
self.llm = ChatGoogleGenerativeAI(
    temperature=0.7,
    max_retries=3,
    request_timeout=30.0,
)

# After
self.llm = ChatGoogleGenerativeAI(
    temperature=settings.DEFAULT_LLM_TEMPERATURE,
    max_retries=settings.DEFAULT_MAX_RETRIES,
    request_timeout=settings.DEFAULT_REQUEST_TIMEOUT,
)
```

**Step 3: Update `.env.example`**:

```bash
# LLM Configuration
DEFAULT_LLM_TEMPERATURE=0.7
DEFAULT_REQUEST_TIMEOUT=30.0

# Image Dimensions
IMAGE_WIDTH_9_16=1080
IMAGE_HEIGHT_9_16=1920
```

## Files Affected

- `src/core/config.py` - Add new settings
- `src/agents/story_finder/agent.py` - Use settings
- `src/agents/script_writer/agent.py` - Use settings
- `src/agents/director/agent.py` - Use settings
- `src/agents/image_gen/agent.py` - Use settings
- `.env.example` - Document new settings

## Success Criteria

- [ ] All hardcoded values moved to settings
- [ ] Settings documented in `.env.example`
- [ ] All tests pass
- [ ] Configuration guide updated

---

**Estimated Effort**: 1-2 days  
**Priority**: Medium  
**Risk**: Low  
**ROI**: Medium (easier configuration)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **12-Factor App**: Configuration should be stored in the environment, not code.
- **Operational Flexibility**: Allows changing timeouts or retry limits without redeploying code (just restart with new env vars).
- **Consistency**: Ensures all agents use the same default values.

**Implementation Phase:** Phase 1 - Foundation & Quality
**Sequence Order:** #2 in implementation queue (Parallel with Base Class)

**Architectural Guidance:**
Key considerations for implementation:
- **Defaults**: Ensure sensible defaults are provided in the Pydantic model so the app works out-of-the-box without a massive `.env` file.
- **Validation**: Use Pydantic's `Field` constraints (e.g., `ge=0.0`, `le=1.0` for temperature) to catch bad config early.
- **Grouping**: Consider grouping settings in the `Settings` class (e.g., nested models) if the list gets too long, though flat is fine for now.

**Dependencies:**
- **Must complete first**: None
- **Should complete first**: None
- **Blocks**: TICKET-036 (Base Class) - Ideally, `BaseAgent` uses these new settings.

**Risk Mitigation:**
- **Environment Variables**: Ensure the new env vars are documented in `.env.example`.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Pydantic validation rules added for all new settings.

**Alternative Approaches Considered:**
- **Selected approach:** Centralized `Settings` object (Pydantic).

**Implementation Notes:**
- Update `src/core/config.py` first.
- Then update usages.

**Estimated Timeline**: 1-2 days
**Recommended Owner**: Junior/Mid-level Engineer
