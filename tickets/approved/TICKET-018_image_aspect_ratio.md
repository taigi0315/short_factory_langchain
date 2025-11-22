# TICKET-018: Image Aspect Ratio Enforcement

## Problem Statement
The user noted that "created image has different ratio, we should set the ratio in prompt." Consistent aspect ratios are crucial for video production, especially for vertical video (Shorts/Reels/TikTok) which requires 9:16.

## Requirements
1.  **Enforce Aspect Ratio:** All generated images must strictly adhere to the target aspect ratio (default 9:16 for Shorts).
2.  **Prompt Engineering:** Update the image generation prompt to explicitly request the specific aspect ratio (e.g., "vertical 9:16 aspect ratio").
3.  **Configurable Ratio:** Allow the aspect ratio to be configured in settings (e.g., for future landscape video support).

## Technical Approach
*   **`src/agents/image_gen/gemini_image_client.py`**:
    *   Update the prompt construction to append aspect ratio instructions.
    *   Gemini Image generation API might support specific aspect ratio parameters - investigate and implement if available.
*   **`src/core/config.py`**:
    *   Add `IMAGE_ASPECT_RATIO` setting (default "9:16").

## Acceptance Criteria
- [ ] All generated images are vertical (9:16).
- [ ] No images are square or landscape unless configured otherwise.

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-22
**Decision:** ✅ APPROVED

**Strategic Rationale:**
- **Platform Fit:** Vertical video is the dominant format for short-form content (Shorts/Reels).
- **Cost Efficiency:** Generating the wrong ratio wastes tokens and money.

**Implementation Phase:** Phase 1 (Sprint 1)
**Sequence Order:** #3 in implementation queue

**Architectural Guidance:**
- **Native Support:** Don't rely solely on prompts. Check if the Gemini Imagen 3 API has a specific `aspect_ratio` parameter (it usually does). Use that first.
- **Fallback:** If native param fails, use prompt engineering ("vertical 9:16 aspect ratio").

**Dependencies:**
- **None:** Independent task.

**Risk Mitigation:**
- **Risk:** Model ignores aspect ratio instruction.
- **Mitigation:** Implement a post-generation check (using PIL) to verify dimensions. If wrong, crop or regenerate (with backoff).

