# TICKET-017: Audio Quality & Expressiveness

## Problem Statement
The user reported that the audio sounds "robotic" and requested controls for voice tone and mood. While we use ElevenLabs, the current default settings might be too neutral or flat.

## Requirements
1.  **Expose Voice Parameters:** Allow configuration of `stability`, `similarity_boost`, `style`, and `use_speaker_boost` via the `VoiceTone` enum in `models.py`.
2.  **Tone Mapping:** Refine the mapping between `VoiceTone` (e.g., EXCITED, SAD, SERIOUS) and specific ElevenLabs parameter presets to ensure distinct emotional delivery.
3.  **Configurable Defaults:** Allow overriding default voice settings in `.env` or `config.py`.

## Technical Approach
*   **`src/models/models.py`**:
    *   Review `ElevenLabsSettings.for_tone` method.
    *   Tune the presets for each tone to be more distinct (e.g., lower stability for more emotion).
*   **`src/agents/voice/agent.py`**:
    *   Ensure these settings are correctly passed to the ElevenLabs API call.

## Acceptance Criteria
- [ ] "Excited" tone sounds noticeably more dynamic than "Serious" tone.
- [ ] "Sad" tone has appropriate pacing and stability.
- [ ] Users can perceive a difference in delivery based on the selected mood.

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-22
**Decision:** ✅ APPROVED

**Strategic Rationale:**
- **User Experience:** "Robotic" voice is a major detractor for AI video. Improving this directly impacts user retention.
- **Scalability:** Defining a clear mapping now prevents ad-hoc parameter tweaking later.

**Implementation Phase:** Phase 1 (Sprint 1)
**Sequence Order:** #2 in implementation queue

**Architectural Guidance:**
- **Configuration over Hardcoding:** Store the tone mappings in `config.py` or a dedicated `voice_presets.py`, not deep in the agent logic.
- **Testing Strategy:** Create a "Voice Gallery" script that generates the same sentence in all tones. This allows for objective A/B testing of settings.

**Dependencies:**
- **Related work:** TICKET-016 (Video Assembly) - better audio might change durations, but the sync logic handles that.

**Risk Mitigation:**
- **Risk:** Over-tuning makes voices sound unstable or glitchy.
- **Mitigation:** Keep `stability` >= 0.3. Test with long sentences to ensure consistency.

