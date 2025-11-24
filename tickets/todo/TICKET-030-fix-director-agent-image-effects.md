# [TICKET-030] Fix Director Agent Image Effects

## Priority
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
- [ ] Feature Implementation

## Impact Assessment
**Business Impact:**
- **HIGH**: The "Director" feature is currently broken, as all images look static or have the same effect, failing to deliver the promised cinematic experience.

**Technical Impact:**
- Affects: `src/agents/director/agent.py`, `src/agents/video_assembly/agent.py`
- Requires: Ensuring the `camera_movement` or effect metadata is correctly passed and applied during video assembly.

**Effort Estimate:**
- Small (< 1 day)

---

## Problem Description

### Current State
**Status:** Bug
**What's happening:**
The `DirectorAgent` is supposed to assign image effects (e.g., zoom, pan), but the generated video shows the same effect (or no effect) for all images.

**Desired State:**
Each scene should have the specific visual effect (camera movement) assigned by the Director Agent.

---

## Requirements

### Functional Requirements
**FR-1: Effect Assignment**
- `DirectorAgent` MUST correctly output unique `camera_movement` or effect parameters for each scene.

**FR-2: Effect Application**
- `VideoAssemblyAgent` MUST read these parameters and apply the corresponding transformation to the image clip using `moviepy`.
- Supported effects should include: Zoom In, Zoom Out, Pan Left, Pan Right, Static.

---

## Implementation Plan

### Phase 1: Debug & Fix
1.  **Verify Director Output**: Check logs to ensure `DirectorAgent` is actually generating different `camera_movement` values.
2.  **Update Video Assembly**: In `src/agents/video_assembly/agent.py`, implement the logic to apply effects based on the scene's metadata.
    - Map `camera_movement` to specific `moviepy` transformations (e.g., resizing and cropping over time for zoom/pan).

---

## Verification Plan

### Manual Verification
1.  Generate a video with a script that calls for different camera movements.
2.  Watch the output video.
3.  Verify that different scenes have different motion effects (e.g., one zooms in, another pans).
