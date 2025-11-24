# TICKET-026: Fix Script Generation Validation Error & Rate Limiting

## Description
The script generation and image generation processes were failing due to two issues:

### Issue 1: Validation Error (FIXED)
The script generation process was failing because the LLM occasionally outputs `image_style` values that are not valid members of the `ImageStyle` enum (e.g., `'visual_demo'`). 

The `VideoScript` Pydantic model enforced strict enum validation during the parsing phase of the LangChain chain (`VIDEO_SCRIPT_PARSER`). This caused a `ValidationError` to be raised *before* the `_validate_and_fix_script` method in `ScriptWriterAgent` had a chance to run and correct the values.

### Issue 2: Image Generation Rate Limiting (FIXED)
After fixing the validation error, image generation was hitting rate limits because the frontend was generating all scene images in parallel using `Promise.all()`, causing simultaneous API requests to Gemini.

## Error Logs

### Validation Error
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for VideoScript
scenes.2.image_style
  Input should be 'single_character', 'character_with_background', ... [type=enum, input_value='visual_demo', input_type=str]
```

### Rate Limiting (from terminal logs)
All 6 images started generating at the same timestamp (`01:08:07`), indicating parallel execution.

## Solutions Implemented

### Fix 1: Robust Field Validators (`src/models/models.py`)

Added `field_validator`s with `mode='before'` to the `Scene` model for:
- `scene_type`
- `voice_tone`  
- `image_style`

These validators:
1. Check if the value is already a valid Enum
2. If it's a string, try to convert it to the Enum
3. If conversion fails, check a `fixes` dictionary for known mappings (e.g., `'visual_demo'` → `ImageStyle.STEP_BY_STEP_VISUAL`)
4. If no mapping is found, log a warning and return a safe default (e.g., `ImageStyle.CINEMATIC`)

### Fix 2: Sequential Image Generation (`frontend/src/app/page.tsx`)

Replaced parallel `Promise.all()` with sequential processing:
- Generate images one at a time in a `for` loop
- Add 2-second delay between requests using `setTimeout`
- Show progress in console: `[1/6] Generating image for scene 1...`

## Acceptance Criteria
- [x] `generate_script` does not raise `ValidationError` for known invalid enum outputs like `'visual_demo'`
- [x] Invalid values are automatically mapped to the nearest valid Enum member
- [x] The full flow produces a valid `VideoScript` object
- [x] Images are generated sequentially with delays to prevent rate limiting
- [x] Users see real-time progress during image generation

## Verification

### Test Script
Created `scripts/test_ticket_026.py` to verify the validation fix.

**Test Output:**
```
Testing VideoScript validation fix...
Fixed invalid image_style: 'visual_demo' -> 'step_by_step_visual'
Fixed invalid scene_type: 'narrative' -> 'story_telling'
Fixed invalid voice_tone: 'explanation' -> 'serious'
Invalid image_style 'unknown_style' not found in fixes. Defaulting to CINEMATIC.
✅ VideoScript parsed successfully!
✅ All assertions passed!
```

### Manual Testing
Test the full flow with a real script to ensure:
1. Script generation succeeds
2. Images generate sequentially with visible delays
3. No rate limit errors in logs
4. Video generation completes successfully
