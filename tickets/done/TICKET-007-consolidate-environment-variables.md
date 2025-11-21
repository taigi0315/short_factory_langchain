# [TICKET-007] Consolidate Environment Variable Handling for Feature Flags

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
- [ ] Code Duplication

## Impact Assessment
**Business Impact:**
- **MEDIUM**: Configuration is scattered and inconsistent
- Hard to understand what environment variables control system behavior
- Risk of misconfiguration in different environments (dev, staging, prod)
- Developer onboarding is harder - no single place to see all config options

**Technical Impact:**
- Affects: Configuration system, all agents
- Currently have 2 different config systems:
  1. Centralized `settings` object (`src/core/config.py`) - API keys only
  2. Direct `os.getenv()` calls scattered in code - feature flags
- Inconsistent: Some use pydantic-settings, some use direct os access
- Missing: `NANO_BANANA_API_KEY`, `USE_REAL_LLM`, `USE_REAL_IMAGE` not in Settings

**Effort Estimate:**
- Small (< 1 day) - 2-3 hours

## Problem Description

### Current State

**Two configuration systems exist:**

**System 1: Centralized Settings** (`src/core/config.py`)
```python
class Settings(BaseSettings):
    llm_model_name: str = Field("gemini-1.5-flash", env="LLM_MODEL_NAME")
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    MAX_VIDEO_SCENES: int = Field(8, env="MAX_VIDEO_SCENES")

settings = Settings()
```

**System 2: Direct `os.getenv()` calls scattered in code:**
- `src/agents/story_finder/agent.py:8` - `os.getenv("USE_REAL_LLM", "false")`
- `src/agents/image_gen/agent.py:9` - `os.getenv("USE_REAL_IMAGE", "false")`
- Plus any NanoBanana configuration is hardcoded or missing

**Missing from Settings:**
- `NANO_BANANA_API_KEY`
- `NANO_BANANA_API_URL`
- `USE_REAL_LLM` (boolean feature flag)
- `USE_REAL_IMAGE` (boolean feature flag)
- `USE_REAL_VOICE` (for future ElevenLabs integration)
- `MOCK_MODE` (global override)
- Output directories (`GENERATED_ASSETS_DIR`)

**Problems:**
1. **Scattered configuration**: No single source of truth
2. **Type inconsistency**: `os.getenv()` returns strings, agents parse "true"/"false" manually
3. **No validation**: Typos in env var names fail silently
4. **Documentation gap**: .env.example doesn't list all variables
5. **Testing difficulty**: Can't easily override config for tests

### Root Cause Analysis
The Settings class was created early for API keys, but feature flags were added later during refactoring without updating the centralized config. This is typical incremental development without periodic consolidation.

### Evidence

**Example 1: ImageGenAgent duplicates config logic**
```python
# src/agents/image_gen/agent.py:8-13
class ImageGenAgent:
    def __init__(self):
        self.mock_mode = os.getenv("USE_REAL_IMAGE", "false").lower() != "true"  # ❌ Manual parsing
        self.api_key = os.getenv("NANO_BANANA_API_KEY")  # ❌ Not in Settings
        self.api_url = os.getenv("NANO_BANANA_API_URL", "https://...")  # ❌ Duplicated default
```

**Example 2: StoryFinderAgent uses same pattern**
```python
# src/agents/story_finder/agent.py:8
self.mock_mode = os.getenv("USE_REAL_LLM", "false").lower() == "true"  # ❌ Duplicate parsing logic
```

**Inconsistent boolean parsing:**
- `image_gen`: `!= "true"` (double negative)
- `story_finder`: `== "true"` (positive check)
- Both should use same validation logic

**Missing .env.example entries:**
```bash
# Current .env.example (presumably)
GEMINI_API_KEY=your_key_here
# ❌ Missing: USE_REAL_LLM, USE_REAL_IMAGE, NANO_BANANA_API_KEY, etc.
```

## Proposed Solution

### Approach
1. Extend `Settings` class with all environment variables
2. Add typed properties with proper defaults
3. Use pydantic validators for boolean fields
4. Update all agents to use `settings` object
5. Create comprehensive `.env.example`

### Implementation Details

**Step 1: Extend Settings class**
```python
# src/core/config.py - AFTER refactoring
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Centralized application configuration.
    All environment variables should be defined here.
    """
    
    # ========================================
    # LLM Configuration
    # ========================================
    llm_model_name: str = Field(
        default="gemini-1.5-flash",
        description="LLM model to use for text generation"
    )
    
    # ========================================
    # API Keys
    # ========================================
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, description="ElevenLabs voice synthesis API key")
    NANO_BANANA_API_KEY: Optional[str] = Field(default=None, description="NanoBanana image generation API key")
    
    # ========================================
    # External Service URLs
    # ========================================
    NANO_BANANA_API_URL: str = Field(
        default="https://api.nanobanana.com/v1/generate",
        description="NanoBanana API endpoint"
    )
    
    # ========================================
    # Feature Flags (Mock vs Real mode)
    # ========================================
    USE_REAL_LLM: bool = Field(
        default=False,
        description="Use real Gemini LLM (true) or mock data (false)"
    )
    USE_REAL_IMAGE: bool = Field(
        default=False,
        description="Use real image generation (true) or placeholders (false)"
    )
    USE_REAL_VOICE: bool = Field(
        default=False,
        description="Use real ElevenLabs (true) or gTTS mock (false)"
    )
    
    # ========================================
    # Application Settings
    # ========================================
    MAX_VIDEO_SCENES: int = Field(default=8, description="Maximum number of scenes per video")
    GENERATED_ASSETS_DIR: str = Field(
        default="generated_assets",
        description="Root directory for generated images/audio/videos"
    )
    
    # ========================================
    # Validators
    # ========================================
    @field_validator('USE_REAL_LLM', 'USE_REAL_IMAGE', 'USE_REAL_VOICE', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Parse boolean from string env vars."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allow USE_REAL_LLM or use_real_llm


settings = Settings()
```

**Step 2: Update agents to use centralized config**
```python
# src/agents/image_gen/agent.py - AFTER refactoring
import os
from typing import List, Dict
from src.models.models import Scene
from src.core.config import settings  # ✅ Import settings
import requests


class ImageGenAgent:
    def __init__(self):
        # ✅ Use centralized config
        self.mock_mode = not settings.USE_REAL_IMAGE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # ✅ API configuration from settings
        self.api_key = settings.NANO_BANANA_API_KEY
        self.api_url = settings.NANO_BANANA_API_URL
    
    # ... rest of implementation
```

```python
# src/agents/story_finder/agent.py - AFTER refactoring
import os  # Still needed for makedirs
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.story_finder.prompts import STORY_FINDER_TEMPLATE, story_parser
from src.agents.story_finder.models import StoryList
from src.core.config import settings  # ✅ Import settings


class StoryFinderAgent:
    def __init__(self):
        # ✅ Single source of truth for LLM config
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7
        )
        self.chain = STORY_FINDER_TEMPLATE | self.llm | story_parser
    
    # ... rest of implementation
```

**Step 3: Create comprehensive .env.example**
```bash
# .env.example - COMPLETE VERSION

# ========================================
# LLM Configuration
# ========================================
LLM_MODEL_NAME=gemini-1.5-flash

# ========================================
# API Keys
# Required for real generation, optional for mock mode
# ========================================
GEMINI_API_KEY=your_gemini_key_here
# OPENAI_API_KEY=your_openai_key_here  # Optional
# ELEVENLABS_API_KEY=your_elevenlabs_key_here  # Optional
# NANO_BANANA_API_KEY=your_nanobanana_key_here  # Optional

# ========================================
# External Service URLs
# Override only if using custom endpoints
# ========================================
# NANO_BANANA_API_URL=https://api.nanobanana.com/v1/generate

# ========================================
# Feature Flags (Mock vs Real Mode)
# Set to 'true' to use real APIs, 'false' for mock/testing
# ========================================
USE_REAL_LLM=false
USE_REAL_IMAGE=false
USE_REAL_VOICE=false

# ========================================
# Application Settings
# ========================================
MAX_VIDEO_SCENES=8
GENERATED_ASSETS_DIR=generated_assets
```

### Alternative Approaches Considered
**Option 1**: Use a separate config file format (YAML/JSON)
- **Why not chosen**: Pydantic-settings with .env is standard in FastAPI ecosystem

**Option 2**: Keep feature flags separate from API keys
- **Why not chosen**: Having everything in one place is simpler for developers

**Option 3**: Use dynaconf or python-decouple
- **Why not chosen**: Pydantic-settings is sufficient and already in use

### Benefits
- ✅ **Single source of truth** for all configuration
- ✅ **Type safety**: Pydantic validates types
- ✅ **Better defaults**: Clear, documented defaults
- ✅ **Easier testing**: Can override settings in tests
- ✅ **Better DX**: `.env.example` shows all available options
- ✅ **Consistency**: All code uses same config pattern
- ✅ **Documentation**: Field descriptions serve as docs

### Risks & Considerations
- Need to update all agent initialization (low risk, mechanical change)
- Tests that use `os.environ` directly will need updating
- Backwards compatible: .env files with old vars still work
- Migration: Existing .env files don't need changes (defaults handle missing values)

## Testing Strategy
**Unit tests:**
```python
# tests/test_config.py
def test_default_values():
    """Test that Settings has sensible defaults."""
    s = Settings()
    assert s.llm_model_name == "gemini-1.5-flash"
    assert s.MAX_VIDEO_SCENES == 8
    assert s.USE_REAL_LLM == False


def test_bool_parsing():
    """Test that boolean env vars parse correctly."""
    import os
    os.environ["USE_REAL_LLM"] = "true"
    s = Settings()
    assert s.USE_REAL_LLM == True
    
    os.environ["USE_REAL_LLM"] = "1"
    s = Settings()
    assert s.USE_REAL_LLM == True


def test_api_key_override():
    """Test that env vars override defaults."""
    import os
    os.environ["GEMINI_API_KEY"] = "test_key"
    s = Settings()
    assert s.GEMINI_API_KEY == "test_key"
```

**Integration tests:**
- Verify agents can be instantiated with various config combos
- Test mock mode vs real mode switching

## Files Affected
**Modified:**
- `src/core/config.py` - Extend Settings class (+40 lines)
- `src/agents/story_finder/agent.py` - Use settings object (lines 8-10)
- `src/agents/script_writer/agent.py` - Already uses settings, no change needed
- `src/agents/image_gen/agent.py` - Use settings object (lines 8-14)
- `src/agents/voice/agent.py` - Add settings usage
- `.env.example` - Add all new variables

**New:**
- `tests/test_config.py` - Config validation tests (~50 lines)

## Dependencies
- Depends on: None
- Blocks: None (but makes other refactorings easier)
- Related to: All agents, TICKET-006 (error handling)

## References
- Pydantic Settings docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- 12-Factor App (config): https://12factor.net/config
- FastAPI settings: https://fastapi.tiangolo.com/advanced/settings/

## Architect Review Questions
1. Should we add environment-specific config files (dev.env, prod.env)?
2. Do we want to expose these settings via a `/config` admin endpoint?
3. Should we validate that required API keys are present on startup (fail fast)?
4. Do we want feature flag management UI or keep it file-based?
5. Should we add observability for which config values are active (logging on startup)?

## Success Criteria
- [x] All environment variables defined in Settings class
- [x] No direct `os.getenv()` calls in agent code
- [x] Boolean parsing is consistent (using validator)
- [x] `.env.example` documents all available variables
- [x] Tests validate config parsing
- [x] All agents use `settings` object
- [x] Configuration is self-documenting (field descriptions)

---

**Impact**: This is foundational work that pays dividends on all future features. Every new agent or feature flag becomes trivial to add with this in place.
