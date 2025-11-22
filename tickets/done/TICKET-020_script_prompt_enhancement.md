# TICKET-020: Script Writer Prompt Enhancement

## Problem Statement
The user requested a review of the legacy prompt (`src/prompts/scrip_writer_agent.py`) to adopt its best practices. The legacy prompt contains detailed guidelines for story structure, hook techniques, and image/video prompting that should be integrated into the current agent.

## Requirements
1.  **Adopt Story Arc Structure:** Enforce the 5-part structure (Hook, Setup, Development, Climax, Resolution) from the legacy prompt.
2.  **Enhance Hook Techniques:** Explicitly include the 5 hook types (Shocking Fact, Intriguing Question, etc.) in the system prompt.
3.  **Refine Image Prompts:** Incorporate the "Image Creation Prompt Guidelines" (lighting, composition, fixed character rules) to improve image consistency.
4.  **Integrate Animation Framework:** Add the "Animation Decision Framework" to help the LLM decide when to set `needs_animation: true`.

## Technical Approach
*   **`src/agents/script_writer/prompts.py`**:
    *   Update the `SCRIPT_WRITER_AGENT_PROMPT` to include sections from the legacy file.
    *   Add the detailed examples for image and video prompts.
    *   Clarify the distinction between `image_style` (visual look) and `hook_technique` (narrative device).

## Acceptance Criteria
- [ ] Generated scripts follow a clear narrative arc.
- [ ] Image prompts are more detailed and consistent (mentioning lighting, composition).
- [ ] The "Hook" scene uses one of the defined techniques effectively.

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-22
**Decision:** ✅ APPROVED

**Strategic Rationale:**
- **Quality Control:** The legacy prompt contained "secret sauce" (detailed guidelines) that was lost. Restoring it improves output quality without code changes.
- **Standardization:** Enforcing structure (Hook, Setup, etc.) makes the video format predictable and professional.

**Implementation Phase:** Phase 1 (Sprint 1)
**Sequence Order:** #5 in implementation queue (can be done in parallel)

**Architectural Guidance:**
- **Prompt Engineering:** Don't just copy-paste. Integrate the legacy logic into the *current* dynamic prompt structure.
- **JSON Stability:** The legacy prompt was text-based. The new one is JSON-based. Ensure the added instructions don't confuse the LLM into outputting invalid JSON.

**Dependencies:**
- **None:** Independent task, but affects TICKET-019 (better video prompts).

**Risk Mitigation:**
- **Risk:** Regression in JSON parsing (LLM becomes too "chatty").
- **Mitigation:** Add a specific regression test case in `tests/` that generates 10 scripts and asserts valid JSON parsing for all.

