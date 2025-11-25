# [TICKET-032] Support Multiple Images per Dialogue

## Priority
- [ ] High (Performance issues, significant tech debt)
- [x] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [ ] Technical Debt
- [ ] Code Duplication
- [x] Feature Implementation

## Impact Assessment
**Business Impact:**
- **MEDIUM**: Allows for more dynamic visual storytelling by breaking up long dialogue segments with multiple images.

**Technical Impact:**
- Affects: `src/models/models.py`, `src/agents/script_writer/agent.py`, `src/agents/video_assembly/agent.py`
- Requires: Schema change to support list of images per scene and logic to split audio duration.

**Effort Estimate:**
- Medium (1-2 days)

---

## Problem Description

### Current State
**Status:** Feature Request
**What's happening:**
Currently, 1 dialogue line = 1 image. If the dialogue is long, the single image is displayed for too long, which is visually boring.

**Desired State:**
The script writer should be able to specify multiple images for a single dialogue line, along with the portion/ratio of time each image should be displayed (e.g., "Image A (10%), Image B (10%), Image C (80%)").

---

## Requirements

### Functional Requirements
**FR-1: Schema Update**
- Update `Scene` model to support a list of image prompts and corresponding duration ratios or segments.

**FR-2: Script Generation**
- `ScriptWriterAgent` MUST be able to generate multiple image prompts for a single scene when appropriate.
- It MUST specify the timing distribution (e.g., ratios or percentages).

**FR-3: Video Assembly**
- `VideoAssemblyAgent` MUST calculate the duration for each image based on the total audio duration and the specified ratios.
- It MUST sequence these images to cover the full duration of the audio clip.

---

## Implementation Plan

### Phase 1: Schema & Agent Updates
1.  **Update Models**: Modify `Scene` in `src/models/models.py` to include `image_prompts: List[str]` and `image_ratios: List[float]`.
2.  **Update Script Writer**: Update prompt to instruct LLM on how/when to generate multiple images.

### Phase 2: Video Assembly
1.  **Update Assembly Logic**: In `src/agents/video_assembly/agent.py`, iterate through the images for a scene.
2.  **Calculate Durations**: `image_duration = total_audio_duration * ratio`.
3.  **Concatenate**: Create a sub-sequence of image clips for the scene and combine with the audio.

---

## Verification Plan

### Manual Verification
1.  Generate a script that produces a scene with multiple images.
2.  Generate the video.
3.  Verify that during the single dialogue line, the video cuts between the specified images at the correct times.
