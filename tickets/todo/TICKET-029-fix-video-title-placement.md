# [TICKET-029] Fix Video Title Placement

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
- **MEDIUM**: Improves the aesthetic quality of the video and matches user expectations.

**Technical Impact:**
- Affects: `src/agents/video_assembly/agent.py`
- Requires: Modifying `moviepy` composition logic.

**Effort Estimate:**
- Small (< 1 day)

---

## Problem Description

### Current State
**Status:** Feature Request / Bug
**What's happening:**
The title of the video currently appears as a separate card or section at the beginning of the video.

**Desired State:**
The user wants the title to be an **overlay** on top of the video content, appearing for the first 3 seconds only.

---

## Requirements

### Functional Requirements
**FR-1: Title Overlay**
- The video title MUST be superimposed over the first scene's video/image.
- The title SHOULD NOT be a separate black screen/card.

**FR-2: Duration**
- The title overlay MUST be visible for the first 3 seconds of the video.

### Non-Functional Requirements
**NFR-1: Aesthetics**
- The title text should be readable (e.g., white text with shadow or outline) regardless of the background video content.

---

## Implementation Plan

### Phase 1: Update Video Assembly
1.  **Modify `VideoAssemblyAgent`**: In `src/agents/video_assembly/agent.py`, locate the clip assembly logic.
2.  **Create TextClip**: Use `moviepy`'s `TextClip` to create the title overlay.
3.  **Composite**: Use `CompositeVideoClip` to layer the text over the first 3 seconds of the video stream.
4.  **Remove Old Title**: Ensure any existing logic that creates a separate title card is removed.

---

## Verification Plan

### Manual Verification
1.  Generate a video.
2.  Watch the first 5 seconds.
3.  Verify the title appears on top of the video content.
4.  Verify the title disappears after 3 seconds.
