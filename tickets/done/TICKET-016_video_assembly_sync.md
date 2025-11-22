# TICKET-016: Video Assembly & Audio Sync Refinement

## Problem Statement
The user requested that "audio and video should be the main, these we can't change the length. for those images, we should `show` as long as audio." Currently, there might be discrepancies where images don't perfectly align with the audio duration, or the system forces a fixed duration.

## Requirements
1.  **Audio-Driven Duration:** The duration of each scene MUST be exactly equal to the duration of its corresponding audio file.
2.  **Visual Synchronization:**
    *   **Static Images:** Must be displayed for the exact duration of the audio.
    *   **Video Clips:** If a video clip is shorter than the audio, it should loop or freeze on the last frame (or slow down). If longer, it should be trimmed.
3.  **Master Timeline:** The total video length should be the sum of all audio clips.

## Technical Approach
*   **`src/agents/video_gen/agent.py`**:
    *   Review `_create_scene_clip` method.
    *   Ensure `AudioFileClip` is the source of truth for duration.
    *   For `ImageClip`, set duration to `audio_clip.duration`.
    *   For `VideoFileClip` (future implementation), implement logic to match `audio_clip.duration`.

## Acceptance Criteria
- [ ] Scene duration exactly matches audio duration.
- [ ] No gaps or overlaps between scenes.
- [ ] Images persist for the full length of the narration.

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-22
**Decision:** ✅ APPROVED

**Strategic Rationale:**
- **Quality Baseline:** Synchronization is fundamental to video quality. Without this, the product feels broken.
- **Foundation:** This logic is required before we introduce more complex AI video elements (TICKET-019).

**Implementation Phase:** Phase 1 (Sprint 1)
**Sequence Order:** #1 in implementation queue

**Architectural Guidance:**
- **Single Source of Truth:** The `AudioFileClip` duration is the master clock. All visual elements must adapt to it.
- **Video Handling Logic:**
    - If video < audio: **Freeze last frame** (Looping can look glitchy for non-seamless loops).
    - If video > audio: **Trim end** (Ensure critical action happens early in the prompt).
- **Performance:** Avoid re-encoding audio if possible; use stream copy if just muxing.

**Dependencies:**
- **Blocks:** TICKET-019 (AI Video Generation) - we need the sync logic before we insert real videos.

**Risk Mitigation:**
- **Risk:** Floating point errors in duration causing black frames.
- **Mitigation:** Use a small epsilon (e.g., 0.05s) overlap or round up visual duration slightly.

---
## ✅ Implementation Complete

**Implemented by:** Implementation Agent
**Implementation Date:** 2025-11-22
**Branch:** feature/ticket-016-video-sync

### What Was Implemented
- Modified `VideoGenAgent._create_scene_clip` to handle video files (`.mp4`, `.mov`, etc.).
- Implemented synchronization logic:
    - **Freeze:** If video < audio, freeze last frame.
    - **Trim:** If video > audio, trim to match audio.
- Added resizing/cropping logic for video clips to match output resolution.
- Verified that `ImageClip` duration is strictly set to audio duration.

### Files Modified
- `src/agents/video_gen/agent.py` - Added video handling and sync logic.

### Files Created
- `tests/unit/test_video_sync.py` - Unit tests for sync logic.
- `tests/__init__.py` - Package marker.
- `tests/unit/__init__.py` - Package marker.

### Tests Added
**Unit Tests:**
- `test_image_sync_with_audio`: Verifies image duration matches audio.
- `test_video_shorter_than_audio`: Verifies short video is frozen/concatenated.

### Verification Performed
- [✓] Unit tests passed (`tests/unit/test_video_sync.py`).
- [✓] Verified logic handles both images and videos.
