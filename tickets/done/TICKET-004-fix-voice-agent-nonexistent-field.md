# [TICKET-004] Fix VoiceAgent Reference to Non-Existent Field audio_narration

## Priority
- [ ] Critical (System stability, security, data loss risk)
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [x] Bug Fix
- [ ] Security Issue
- [ ] Technical Debt
- [ ] Code Duplication

## Impact Assessment
**Business Impact:**
- **HIGH**: Voice generation will use fallback text "No dialogue" for any scene where `dialogue` is None/empty
- Audio quality degraded - scenes without dialogue will have generic placeholder audio instead of actual narration
- Risk: The field `audio_narration` doesn't exist in the `Scene` model, so this code path will AttributeError if `dialogue` is None

**Technical Impact:**
- Affects: `src/agents/voice/agent.py`, voice generation workflow
- Files needing changes: 1 file
- Breaking change: Currently has fallback that masks the error, but produces bad output
- This is technical debt from old model schema that was refactored but not updated in all consumers

**Effort Estimate:**
- Small (< 1 day) - 10 minutes to fix

## Problem Description

### Current State
**Location:** `src/agents/voice/agent.py:27`

The `VoiceAgent.generate_voiceovers()` method references a non-existent field `scene.audio_narration` as a fallback when `scene.dialogue` is None:

```python
# Current buggy code (line 27)
text = scene.dialogue or scene.audio_narration or "No dialogue"
```

**The issue:**
1. The `Scene` model (defined in `src/models/models.py:128-165`) only has a `dialogue` field (line 133)
2. There is NO `audio_narration` field in the current schema
3. If `scene.dialogue` is `None` or empty, the code will try to access `scene.audio_narration` which will raise `AttributeError`
4. This would cause voice generation to fail entirely for scenes without dialogue

**Why this hasn't crashed yet:**
- It appears all current mock/test data includes `dialogue` field populated
- The `or` short-circuit stops at `scene.dialogue` if it's truthy
- If `dialogue` is falsy (None, empty string), it WILL crash

### Root Cause Analysis
This is leftover code from an earlier version of the schema where scenes had both `dialogue` and `audio_narration` fields. During schema refactoring:
- The model was updated to use only `dialogue` (see `Scene` model line 133)
- The frontend was updated to use `dialogue` (see `frontend/src/app/page.tsx`)
- The `VoiceAgent` consumer code was never updated to match

This is a classic refactoring incompleteness issue.

### Evidence
**Scene model definition** (`src/models/models.py:128-135`):
```python
class Scene(BaseModel):
    scene_number: int
    scene_type: SceneType
    
    # Dialogue/narration
    dialogue: Optional[str] = Field(default=None, description="What the character will say")  # ✅ This exists
    voice_tone: VoiceTone
    elevenlabs_settings: ElevenLabsSettings
    # ❌ NO audio_narration field
```

**VoiceAgent buggy reference** (`src/agents/voice/agent.py:27`):
```python
text = scene.dialogue or scene.audio_narration or "No dialogue"  # ❌ audio_narration doesn't exist
```

**Proof it will fail:**
```python
# Test case that would trigger the bug:
scene = Scene(
    scene_number=1,
    scene_type=SceneType.HOOK,
    dialogue=None,  # or ""
    voice_tone=VoiceTone.EXCITED,
    # ... other fields
)
# This will raise: AttributeError: 'Scene' object has no attribute 'audio_narration'
```

## Proposed Solution

### Approach
Simply remove the non-existent field reference and provide a clearer fallback message.

### Implementation Details
```python
# Fixed code (line 27)
text = scene.dialogue if scene.dialogue else "[No dialogue for this scene]"
```

**Or more concisely:**
```python
text = scene.dialogue or "[No dialogue for this scene]"
```

### Alternative Approaches Considered
**Option 1**: Add back `audio_narration` field to Scene model
- **Why not chosen**: The model refactoring was intentional - `dialogue` is the correct single field for spoken content. Adding back audio_narration would create confusion and duplication.

**Option 2**: Use empty string as fallback
- **Why not chosen**: gTTS would generate a very short/invalid audio file for empty string. Better to have a clear spoken message indicating no content.

**Option 3**: Skip voice generation for scenes without dialogue
- **Why not chosen**: This would break the video assembly pipeline which expects audio files for all scenes (matching scene_number keys in the dict).

### Benefits
- ✅ Fixes potential AttributeError crash
- ✅ Provides clear audio feedback when dialogue is missing
- ✅ Aligns code with current schema
- ✅ Makes code more maintainable and clear

### Risks & Considerations
- No breaking changes
- No migration needed
- If scenes intentionally have no dialogue (e.g. music-only), the placeholder audio might need adjustment
- Consider: Should we log a warning when dialogue is missing?

## Testing Strategy
**Unit tests to add:**
```python
# tests/test_voice_agent.py
async def test_generate_voiceover_with_no_dialogue():
    """Test that voice generation handles scenes without dialogue gracefully."""
    agent = VoiceAgent()
    scene = Scene(
        scene_number=1,
        scene_type=SceneType.HOOK,
        dialogue=None,  # No dialogue
        voice_tone=VoiceTone.FRIENDLY,
        # ... other required fields
    )
    audio_paths = await agent.generate_voiceovers([scene])
    
    assert 1 in audio_paths
    assert os.path.exists(audio_paths[1])
    # Verify the audio file was created with fallback text

async def test_generate_voiceover_with_empty_dialogue():
    """Test that voice generation handles empty string dialogue."""
    # Similar to above but with dialogue=""
    pass
```

**Integration tests:**
- Add a scene with `dialogue=None` to integration test script
- Verify video generation completes without error
- Verify audio file is generated with placeholder text

## Files Affected
- `src/agents/voice/agent.py` (line 27) - Remove `audio_narration` reference

## Dependencies
- Depends on: None
- Blocks: None (but prevents future crashes)
- Related to: Scene model refactoring (historical)

## References
- Current Scene model: `src/models/models.py:128-165`
- Frontend uses `dialogue`: `frontend/src/app/page.tsx:239` (shows only dialogue field)
- gTTS documentation: https://gtts.readthedocs.io/

## Architect Review Questions
**For the architect to consider:**
1. Should we enforce that `dialogue` is always required (non-Optional) in the Scene model?
2. Do we want special handling for "silent" scenes (music only, no narration)?
3. Should we add validation to ensure every scene has either dialogue OR a marker that it's intentionally silent?
4. Is "[No dialogue for this scene]" the right fallback message, or should it be configurable?

## Success Criteria
- [x] Code no longer references non-existent `audio_narration` field
- [x] Voice generation works for scenes with `dialogue=None`
- [x] Voice generation works for scenes with `dialogue=""`
- [x] Clear, understandable fallback audio is generated
- [x] No AttributeError crashes
- [x] Integration tests pass with dialogue-less scenes

---

**Priority Note**: While not immediately crashing (due to current data always having dialogue), this is HIGH priority because:
1. It's a ticking time bomb - will crash as soon as someone creates a scene without dialogue
2. It represents incomplete refactoring that could confuse future developers
3. Easy fix with high confidence
