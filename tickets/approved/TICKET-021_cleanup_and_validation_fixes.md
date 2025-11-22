# TICKET-021: Project Cleanup & LLM Validation Fixes

**Created:** 2025-11-22  
**Status:** APPROVED  
**Priority:** HIGH  
**Effort:** 1-2 days  
**Owner:** Backend Engineer

---

## Problem Statement

### Issue 1: LLM Validation Errors

**Current State:**
The LLM is generating invalid enum values that fail Pydantic validation:
- `voice_tone` receiving `'explanation'` instead of valid VoiceTone values
- `scene_type` receiving `'climax'` instead of valid SceneType values
- Script generation falling back to mock data due to validation failures

**Error Example:**
```
scenes.2.voice_tone
  Input should be 'excited', 'curious', 'serious', 'friendly', 'sad', 
  'mysterious', 'surprised', 'confident', 'worried', 'playful', 'dramatic', 
  'calm', 'enthusiastic' or 'sarcastic' [type=enum, input_value='explanation']

scenes.6.scene_type
  Input should be 'explanation', 'visual_demo', 'comparison', 'story_telling', 
  'hook' or 'conclusion' [type=enum, input_value='climax']
```

**Root Cause:**
1. LLM is confusing field names with enum values
2. Prompt may not be clear enough about enum constraints
3. LLM might be using outdated or creative values

### Issue 2: MIN_SCENES Not Enforced

**Current State:**
- `MIN_SCENES` is set to 4 in config
- LLM is generating only 2 scenes
- No validation enforcing minimum scene count

**Expected Behavior:**
- Generated scripts should have at least `MIN_SCENES` scenes
- Validation should reject scripts with too few scenes

### Issue 3: Root Directory Clutter

**Current State:**
Root directory contains 20+ files including:
- Documentation files: `project_knowledge_transfer.md`, `CLAUDE.md`, `DEVELOPER_GUIDE.md`, `CONTRIBUTING.md`
- Config files: `docker-compose.yml`, `Dockerfile`, `.dockerignore`
- Utility scripts: `test_logging.py`, `convert_logging.py`, `demo.py`
- Notebooks: `AIVCP.ipynb`
- Setup files: `setup.py`, `Makefile`, `requirements.txt`

**Problems:**
- Difficult to navigate
- Unclear project structure
- Will get worse with future development
- Violates clean architecture principles

---

## Proposed Solution

### Part 1: Fix LLM Validation Errors

#### 1.1 Enhance Script Writer Prompt

**File:** `src/agents/script_writer/prompts.py`

**Changes:**
```python
# Add explicit enum value examples and warnings
ENUM_VALIDATION_SECTION = """
⚠️ CRITICAL: ENUM VALUE VALIDATION ⚠️

You MUST use EXACTLY these values (case-sensitive):

**voice_tone** - Use these EXACT values:
- excited, curious, serious, friendly, sad, mysterious, surprised
- confident, worried, playful, dramatic, calm, enthusiastic, sarcastic

**scene_type** - Use these EXACT values:
- explanation, visual_demo, comparison, story_telling, hook, conclusion

❌ NEVER use these invalid values:
- For voice_tone: "explanation", "climax", "narrative" (these are scene types!)
- For scene_type: "climax", "rising_action", "development" (not in our enum!)

✅ CORRECT Example:
{
  "scene_type": "explanation",  // ← Valid SceneType
  "voice_tone": "curious"        // ← Valid VoiceTone
}

❌ WRONG Example:
{
  "scene_type": "climax",        // ← INVALID! Use "explanation" or "conclusion"
  "voice_tone": "explanation"    // ← INVALID! Use "serious" or "curious"
}
"""
```

#### 1.2 Add Post-Generation Validation

**File:** `src/agents/script_writer/agent.py`

```python
def _validate_and_fix_script(self, script: VideoScript) -> VideoScript:
    """
    Validate script and attempt to fix common LLM errors.
    
    Fixes:
    - Invalid voice_tone values → map to closest valid tone
    - Invalid scene_type values → map to closest valid type
    - Too few scenes → raise error
    """
    # Mapping for common LLM mistakes
    voice_tone_fixes = {
        "explanation": VoiceTone.SERIOUS,
        "narrative": VoiceTone.CALM,
        "climax": VoiceTone.DRAMATIC,
        "development": VoiceTone.CURIOUS
    }
    
    scene_type_fixes = {
        "climax": SceneType.CONCLUSION,
        "rising_action": SceneType.EXPLANATION,
        "development": SceneType.EXPLANATION,
        "resolution": SceneType.CONCLUSION
    }
    
    # Validate scene count
    if len(script.scenes) < settings.MIN_SCENES:
        raise ValueError(
            f"Script has {len(script.scenes)} scenes, "
            f"minimum is {settings.MIN_SCENES}"
        )
    
    # Fix invalid enum values
    for scene in script.scenes:
        # Fix voice_tone if invalid
        if isinstance(scene.voice_tone, str):
            if scene.voice_tone in voice_tone_fixes:
                logger.warning(
                    f"Fixed invalid voice_tone '{scene.voice_tone}' "
                    f"to '{voice_tone_fixes[scene.voice_tone]}'"
                )
                scene.voice_tone = voice_tone_fixes[scene.voice_tone]
        
        # Fix scene_type if invalid
        if isinstance(scene.scene_type, str):
            if scene.scene_type in scene_type_fixes:
                logger.warning(
                    f"Fixed invalid scene_type '{scene.scene_type}' "
                    f"to '{scene_type_fixes[scene.scene_type]}'"
                )
                scene.scene_type = scene_type_fixes[scene.scene_type]
    
    return script
```

#### 1.3 Add Retry Logic with Feedback

```python
async def generate_script_with_retry(
    self,
    topic: str,
    language: str = "English",
    max_scenes: int = None,
    max_retries: int = 3
) -> VideoScript:
    """Generate script with automatic retry on validation errors."""
    
    for attempt in range(max_retries):
        try:
            script = await self.generate_script(topic, language, max_scenes)
            script = self._validate_and_fix_script(script)
            return script
            
        except ValidationError as e:
            if attempt == max_retries - 1:
                raise
            
            logger.warning(
                f"Validation failed (attempt {attempt + 1}/{max_retries})",
                errors=str(e)
            )
            
            # Add validation errors to next prompt as feedback
            error_feedback = self._format_validation_errors(e)
            # Retry with enhanced prompt including error feedback
```

---

### Part 2: Enforce MIN_SCENES

#### 2.1 Update Prompt Template

```python
# In create_dynamic_prompt()
prompt += f"""
**Scene Count Requirements:**
- You MUST generate between {settings.MIN_SCENES} and {max_video_scenes} scenes
- MINIMUM: {settings.MIN_SCENES} scenes (this is REQUIRED)
- MAXIMUM: {max_video_scenes} scenes
- Generating fewer than {settings.MIN_SCENES} scenes will cause validation failure
"""
```

#### 2.2 Add Pydantic Validator

**File:** `src/models/models.py`

```python
class VideoScript(BaseModel):
    # ... existing fields ...
    
    @field_validator('scenes')
    @classmethod
    def validate_scene_count(cls, v, info):
        """Ensure scene count is within MIN_SCENES and MAX_SCENES."""
        from src.core.config import settings
        
        scene_count = len(v)
        
        if scene_count < settings.MIN_SCENES:
            raise ValueError(
                f"Script must have at least {settings.MIN_SCENES} scenes, "
                f"got {scene_count}"
            )
        
        if scene_count > settings.MAX_SCENES:
            raise ValueError(
                f"Script must have at most {settings.MAX_SCENES} scenes, "
                f"got {scene_count}"
            )
        
        return v
```

---

### Part 3: Reorganize Project Structure

#### 3.1 New Directory Structure

```
ShortFactoryLangChain/
├── .github/                    # GitHub workflows (keep)
├── docs/                       # All documentation
│   ├── architecture/           # NEW: Architecture docs
│   │   ├── system_overview.md
│   │   └── data_models.md
│   ├── guides/                 # NEW: User guides
│   │   ├── DEVELOPER_GUIDE.md (moved)
│   │   ├── CONTRIBUTING.md    (moved)
│   │   └── DEPLOYMENT.md
│   ├── api/                    # API docs (existing)
│   └── knowledge/              # NEW: Knowledge transfer
│       └── project_knowledge_transfer.md (moved)
│
├── scripts/                    # Utility scripts
│   ├── test_logging.py        (moved)
│   ├── convert_logging.py     (moved)
│   ├── demo.py                (moved)
│   └── generate_voice_gallery.py (existing)
│
├── notebooks/                  # Jupyter notebooks
│   └── AIVCP.ipynb            (moved)
│
├── docker/                     # NEW: Docker files
│   ├── Dockerfile             (moved)
│   ├── docker-compose.yml     (moved)
│   └── .dockerignore          (moved)
│
├── config/                     # NEW: Config examples
│   └── .env.example           (moved)
│
├── src/                        # Source code (keep)
├── tests/                      # Tests (keep)
├── frontend/                   # Frontend (keep)
├── generated_assets/           # Generated files (keep)
├── tickets/                    # Tickets (keep)
│
├── .env                        # Environment (keep in root)
├── .gitignore                  # Git config (keep in root)
├── README.md                   # Main readme (keep in root)
├── requirements.txt            # Dependencies (keep in root)
├── setup.py                    # Setup (keep in root)
├── Makefile                    # Build commands (keep in root)
└── start_dev.sh                # Dev script (keep in root)
```

#### 3.2 Migration Script

**File:** `scripts/reorganize_project.py`

```python
#!/usr/bin/env python3
"""
Reorganize project structure for better maintainability.
"""

import shutil
from pathlib import Path

MOVES = {
    # Documentation
    "project_knowledge_transfer.md": "docs/knowledge/project_knowledge_transfer.md",
    "DEVELOPER_GUIDE.md": "docs/guides/DEVELOPER_GUIDE.md",
    "CONTRIBUTING.md": "docs/guides/CONTRIBUTING.md",
    "CLAUDE.md": "docs/guides/CLAUDE.md",
    
    # Scripts
    "test_logging.py": "scripts/test_logging.py",
    "convert_logging.py": "scripts/convert_logging.py",
    "demo.py": "scripts/demo.py",
    
    # Docker
    "Dockerfile": "docker/Dockerfile",
    "docker-compose.yml": "docker/docker-compose.yml",
    ".dockerignore": "docker/.dockerignore",
    
    # Notebooks
    "AIVCP.ipynb": "notebooks/AIVCP.ipynb",
    
    # Config
    ".env.example": "config/.env.example",
}

def reorganize():
    """Execute reorganization."""
    root = Path(__file__).parent.parent
    
    for src, dst in MOVES.items():
        src_path = root / src
        dst_path = root / dst
        
        if not src_path.exists():
            print(f"⚠️  Skip: {src} (not found)")
            continue
        
        # Create destination directory
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(src_path), str(dst_path))
        print(f"✅ Moved: {src} → {dst}")
    
    print("\n✨ Reorganization complete!")

if __name__ == "__main__":
    reorganize()
```

#### 3.3 Update Import Paths

After reorganization, update:
- `Makefile` - Update docker paths
- `start_dev.sh` - Update script paths
- `README.md` - Update documentation links
- `.gitignore` - Update ignore patterns if needed

---

## Implementation Plan

### Phase 1: Fix LLM Validation (4 hours)

1. **Update Script Writer Prompt** (1 hour)
   - Add ENUM_VALIDATION_SECTION
   - Add explicit examples
   - Add warnings about common mistakes

2. **Add Validation & Fixing Logic** (2 hours)
   - Implement `_validate_and_fix_script()`
   - Add retry logic with feedback
   - Add logging for fixes

3. **Add MIN_SCENES Enforcement** (1 hour)
   - Update prompt template
   - Add Pydantic validator
   - Test with various scene counts

### Phase 2: Project Reorganization (3 hours)

1. **Create New Directories** (30 min)
   - `docs/architecture/`
   - `docs/guides/`
   - `docs/knowledge/`
   - `docker/`
   - `config/`

2. **Create Migration Script** (1 hour)
   - Write `scripts/reorganize_project.py`
   - Test in dry-run mode
   - Execute migration

3. **Update References** (1.5 hours)
   - Update Makefile
   - Update start_dev.sh
   - Update README.md
   - Update import paths
   - Update documentation links

### Phase 3: Testing & Verification (1 hour)

1. **Test LLM Validation**
   - Generate 10 test scripts
   - Verify no validation errors
   - Verify MIN_SCENES enforcement

2. **Test Project Structure**
   - Verify all files moved correctly
   - Test `./start_dev.sh`
   - Test `make` commands
   - Verify documentation links

---

## Success Criteria

- [ ] LLM generates valid enum values (0 validation errors in 10 test runs)
- [ ] Scripts always have >= MIN_SCENES scenes
- [ ] Validation errors are automatically fixed when possible
- [ ] Root directory has <= 10 files (down from 20+)
- [ ] All documentation in `docs/` subdirectories
- [ ] All scripts in `scripts/` directory
- [ ] Docker files in `docker/` directory
- [ ] All existing functionality still works
- [ ] Documentation links updated
- [ ] No broken imports

---

## Testing Strategy

### LLM Validation Tests

```python
# tests/unit/test_llm_validation_fixes.py

@pytest.mark.asyncio
async def test_script_has_minimum_scenes():
    """Test that generated scripts have at least MIN_SCENES."""
    agent = ScriptWriterAgent()
    
    script = await agent.generate_script(
        topic="Why is the sky blue?",
        language="English"
    )
    
    assert len(script.scenes) >= settings.MIN_SCENES

@pytest.mark.asyncio
async def test_enum_validation_fix():
    """Test that invalid enum values are fixed."""
    agent = ScriptWriterAgent()
    
    # Create script with invalid values
    invalid_script = VideoScript(
        title="Test",
        main_character_description="Test char",
        overall_style="test",
        scenes=[
            Scene(
                scene_number=1,
                scene_type="climax",  # Invalid!
                voice_tone="explanation",  # Invalid!
                # ... other fields
            )
        ]
    )
    
    # Should fix invalid values
    fixed = agent._validate_and_fix_script(invalid_script)
    
    assert fixed.scenes[0].scene_type == SceneType.CONCLUSION
    assert fixed.scenes[0].voice_tone == VoiceTone.SERIOUS
```

### Project Structure Tests

```bash
# Test that files are in correct locations
test -f docs/guides/DEVELOPER_GUIDE.md
test -f docker/Dockerfile
test -f scripts/test_logging.py

# Test that dev environment still works
./start_dev.sh &
sleep 5
curl http://localhost:8000/health
```

---

## Files Affected

**Modified:**
- `src/agents/script_writer/prompts.py` - Enhanced validation section
- `src/agents/script_writer/agent.py` - Add validation & retry logic
- `src/models/models.py` - Add scene count validator
- `Makefile` - Update docker paths
- `start_dev.sh` - Update script paths
- `README.md` - Update documentation links

**New:**
- `scripts/reorganize_project.py` - Migration script
- `tests/unit/test_llm_validation_fixes.py` - Validation tests
- `docs/architecture/` - New directory
- `docs/guides/` - New directory
- `docs/knowledge/` - New directory
- `docker/` - New directory
- `config/` - New directory

**Moved:**
- 13 files moved to new locations (see Part 3.1)

---

## Dependencies

- None (internal refactoring only)

---

## Risks & Mitigation

### Risk: Breaking Existing Functionality

**Mitigation:**
- Test thoroughly after each phase
- Keep git history for easy rollback
- Update all references systematically

### Risk: LLM Still Generates Invalid Values

**Mitigation:**
- Implement automatic fixing
- Add retry logic
- Log all fixes for monitoring
- Consider fine-tuning prompt further

### Risk: Import Path Issues After Reorganization

**Mitigation:**
- Use migration script
- Test all imports
- Update systematically
- Document all changes

---

## Priority: HIGH

**Rationale:**
- LLM validation errors block video generation (user-facing bug)
- Project organization affects developer productivity
- Both issues will worsen without intervention

---

**Estimated Timeline:** 1-2 days  
**Recommended Owner:** Backend engineer familiar with LangChain and project structure
