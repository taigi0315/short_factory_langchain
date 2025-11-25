# Feature Ticket: Refactor Agent Architecture & Activate Director

**Priority:** High
**Component:** Backend / Agent Orchestration
**Type:** Refactor / Enhancement

## 1. Context & Objective
The current video generation pipeline overloads the **Script Writer** with visual duties and leaves the **Director Agent** unused. This results in suboptimal scripts and generic visuals. We aim to implement a "Chain of Command" architecture where each agent has a specialized role.

## 2. Target Architecture
`StoryFinder` -> `ScriptWriter` -> `Director` -> (`ImageGen`, `Voice`) -> `VideoAssembly`

## 3. Implementation Steps

### Phase 1: Activate Director Agent
- [ ] Refactor `DirectorAgent` to accept `VideoScript` and output `DirectedScript`.
- [ ] Ensure `DirectedScript` contains detailed `image_prompts` (replacing Script Writer's prompts).
- [ ] Ensure `DirectedScript` contains `video_effects` mapped from camera movements.

### Phase 2: Specialize Script Writer
- [ ] Update `ScriptWriter` prompts to remove visual engineering instructions.
- [ ] Focus `ScriptWriter` on narrative structure, dialogue, and pacing.

### Phase 3: Update Downstream Agents
- [ ] Update `ImageGenAgent` to use prompts from `DirectedScript`.
- [ ] Update `VideoAssemblyAgent` to apply effects defined by `DirectorAgent`.

### Phase 4: Orchestration
- [ ] Rewrite `src/api/routes/videos.py` to implement the new chain.
- [ ] (Optional) Integrate `StoryFinder` as the initial step in the route.

## 4. Acceptance Criteria
- [ ] The `/generate` endpoint successfully runs the full chain: Script -> Director -> Assets -> Video.
- [ ] Generated videos demonstrate distinct visual styles defined by the Director (not just generic styles).
- [ ] Script Writer output is purely narrative/dialogue focused.
- [ ] Unit tests pass for the new orchestration flow.
