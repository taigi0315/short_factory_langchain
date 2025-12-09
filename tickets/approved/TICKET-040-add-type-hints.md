# [TICKET-040] Add Missing Type Hints and Improve Type Safety

## Priority
- [ ] Critical
- [x] High
- [ ] Medium
- [ ] Low

## Type
- [x] Refactoring
- [x] Technical Debt

## Impact Assessment

**Business Impact**: Better IDE support, fewer type-related bugs, easier onboarding

**Technical Impact**:
- Modules Affected: All agents, API routes, core modules
- Files to Change: ~20 files
- Type Hint Coverage: From ~70% to 100% for public APIs
- Breaking Changes: None (additive only)

**Effort Estimate**: Medium (2 days)

## Problem Description

### Current State

Many functions missing type hints, especially:
- Return types on async functions
- Complex type annotations (Dict, List, Optional)
- Generic types for Pydantic models

**Example** (from image_gen/agent.py:204):
```python
async def _generate_scene_images(self, client, scene):  # Missing types
    """Generate one or more images for a single scene based on visual segments."""
    prompts = []
    # ...
```

**Should be**:
```python
async def _generate_scene_images(
    self,
    client: GeminiImageClient,
    scene: Scene
) -> List[str]:
    """Generate one or more images for a single scene based on visual segments."""
    prompts: List[str] = []
    # ...
```

### Root Cause

- Type hints added inconsistently
- No type checking in development
- No CI/CD enforcement

## Proposed Solution

### Implementation

1. **Add type hints to all public methods**
2. **Add type hints to critical private methods**
3. **Configure mypy for type checking**
4. **Add mypy to CI/CD**

**Example Refactoring**:

```python
from typing import List, Dict, Optional
from src.models.models import Scene
from src.agents.image_gen.gemini_image_client import GeminiImageClient

class ImageGenAgent:
    def __init__(self) -> None:
        self.mock_mode: bool = not settings.USE_REAL_IMAGE
        self.output_dir: str = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        # ...
    
    async def generate_images(
        self,
        scenes: List[Scene],
        workflow_id: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """Generate images for scenes."""
        # ...
    
    async def _generate_scene_images(
        self,
        client: GeminiImageClient,
        scene: Scene
    ) -> List[str]:
        """Generate images for a single scene."""
        # ...
    
    def _cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key."""
        return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()[:16]
```

**mypy Configuration** (`mypy.ini`):

```ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start lenient
disallow_untyped_calls = False
check_untyped_defs = True

[mypy-src.agents.*]
disallow_untyped_defs = True  # Strict for agents

[mypy-tests.*]
disallow_untyped_defs = False  # Lenient for tests
```

## Testing Strategy

- Run `mypy src/` to check types
- Fix all type errors
- Add mypy to CI/CD pipeline
- Gradually increase strictness

## Files Affected

**High Priority** (public APIs):
- `src/agents/*/agent.py` (7 files)
- `src/api/routes/*.py` (5 files)
- `src/core/*.py` (3 files)

**Medium Priority** (internal):
- `src/agents/*/models.py`
- `src/agents/*/prompts.py`

## Dependencies

- **Depends on**: None
- **Blocks**: None
- **Related to**: TICKET-036 (Base Class)

## Success Criteria

- [ ] 100% type hint coverage for public APIs
- [ ] mypy configured and passing
- [ ] mypy in CI/CD
- [ ] No type errors in codebase
- [ ] Documentation updated

---

**Estimated Effort**: 2 days  
**Priority**: High  
**Risk**: Low  
**ROI**: Medium (better IDE support, fewer bugs)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **Safety**: Python's dynamic nature is great for prototyping, but for a complex system like this, type hints provide a necessary safety rail.
- **Documentation**: Type hints are the best form of documentation. They never get out of date (because the type checker fails).
- **Tooling**: Enables better IDE support (autocompletion, refactoring tools).

**Implementation Phase:** Phase 2 - Reliability & Standardization
**Sequence Order:** #5 in implementation queue (Can be done in parallel with others)

**Architectural Guidance:**
Key considerations for implementation:
- **Gradual Adoption**: Don't try to fix everything at once. Start with `src/core` and `src/models`, then `src/agents`.
- **Generics**: Use `list[str]` instead of `List[str]` (Python 3.9+ standard) if possible, unless we are constrained to older versions. The project seems to use Python 3.12 (based on mypy config proposal), so use the built-in types.
- **Pydantic**: Leverage Pydantic models where possible instead of raw dictionaries.

**Dependencies:**
- **Must complete first**: None
- **Should complete first**: TICKET-036 (Base Class) - easier to type hint the new base class once than 7 old classes.
- **Blocks**: None

**Risk Mitigation:**
- **Circular Imports**: Adding type hints often exposes circular dependency issues. Be prepared to use `TYPE_CHECKING` blocks or string forward references.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Use modern Python 3.10+ type syntax (`str | int` instead of `Union[str, int]`, `list[str]` instead of `List[str]`).

**Alternative Approaches Considered:**
- **Selected approach:** Strict typing for core/agents, lenient for tests.

**Implementation Notes:**
- Create `mypy.ini` first.
- Run `mypy` and fix errors module by module.

**Estimated Timeline**: 2 days
**Recommended Owner**: Any Engineer
