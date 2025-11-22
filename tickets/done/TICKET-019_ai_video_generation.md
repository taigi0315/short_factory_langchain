# TICKET-019: AI Video Generation Integration

## Problem Statement
The user requested: "for those 'important' parts, we should create real video using AI as well. using AI, image+text to video." Currently, we only use static images with Ken Burns effects.

## Requirements
1.  **Selective Video Generation:** Only generate expensive AI video for scenes marked as `needs_animation: true` (or "important").
2.  **Image-to-Video:** Use the generated image as the first frame (Image-to-Video) to ensure consistency.
3.  **Video Prompts:** Use the `video_prompt` field from the script to guide the motion.
4.  **Integration:** Integrate with a video generation API (e.g., Runway Gen-2, Pika, Stability Video, or Luma). *Note: Need to select a provider.*

## Technical Approach
*   **`src/agents/video_gen/agent.py`**:
    *   Add a new method `generate_ai_video(image_path, prompt)`.
    *   In `_create_scene_clip`, check if `scene.needs_animation` is true.
    *   If true, call `generate_ai_video` instead of creating a static clip.
*   **Provider Selection:**
    *   Investigate available APIs (Runway, Stability, Luma).
    *   Implement a client for the chosen provider.

## Acceptance Criteria
- [ ] "Important" scenes are rendered as 3-4 second video clips.
- [ ] Video clips match the style and content of the source image.
- [ ] Static scenes remain as images (to save cost/time).

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-22
**Decision:** ✅ APPROVED (with phased approach)

**Strategic Rationale:**
- **Competitive Advantage:** Moving from static images to video is the next logical step for "premium" output.
- **Cost Management:** Selective generation (only "important" scenes) is the right architectural pattern to manage high API costs.

**Implementation Phase:** Phase 2 (Sprint 2)
**Sequence Order:** #4 in implementation queue

**Architectural Guidance:**
- **Phase 1 (Selection):** Do not commit to a provider immediately. Create a small prototype script to test Runway Gen-2, Pika, and Luma using the *same* source image. Evaluate consistency, cost, and latency.
- **Phase 2 (Integration):** Implement the winner.
- **Abstraction:** Create a `VideoGenerationProvider` abstract base class. This allows us to switch providers later (e.g., if OpenAI Sora becomes available) without rewriting the agent.

**Dependencies:**
- **Must complete first:** TICKET-016 (Video Assembly) - we need the sync logic to handle variable video clip lengths.

**Risk Mitigation:**
- **Risk:** API latency (video gen takes 30s+).
- **Mitigation:** Ensure the frontend timeout (TICKET-015) is sufficient. Implement async polling for video generation status.

