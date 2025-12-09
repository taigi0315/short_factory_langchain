# [TICKET-045] Enforce Consistent Video Style

## Priority
- [ ] Critical
- [ ] High
- [x] Medium
- [ ] Low

## Type
- [ ] Bug Fix
- [ ] Refactoring
- [x] Feature

## Impact Assessment
**Business Impact**: Professional, cohesive look for the video.
**Technical Impact**: `DirectorAgent`, `ImageGenAgent`
**Effort Estimate**: Medium (2-3 hours)

## Problem Description
The user noted that image styles vary too much within a single video. While some variety is needed (e.g., for diagrams), the general aesthetic (photorealistic, cinematic, comic, etc.) should be consistent.

## Proposed Solution
1. **Global Style Parameter**: Introduce a `global_style` parameter in `VideoScript` or `DirectedScript`.
2. **Director Logic Update**: Update `DirectorAgent` to pick a "Primary Style" for the video (or accept one from input). Use this primary style for *most* scenes.
3. **Selective Override**: Allow specific scene types (e.g., `EXPLANATION` with `DIAGRAM`) to override the global style, but ensure the transition isn't too jarring (maybe keep lighting inconsistent?).
4. **Prompt Consistency**: Ensure the "style suffix" used in `ImageGenAgent` is identical for all consistent scenes.

## Files Affected
- `src/agents/director/agent.py`
- `src/agents/image_gen/agent.py`
- `src/models/models.py` (Script model updates)

## Success Criteria
- [ ] Generated videos have a cohesive visual theme.
- [ ] Exceptions (diagrams) are handled gracefully but don't break the immersion.
