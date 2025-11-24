# [TICKET-031] Improve Script Writer (Prompt Switching & Quality)

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
- **MEDIUM**: Users are unsatisfied with the current story quality. Tailoring prompts to specific story types (tags) will improve engagement.

**Technical Impact:**
- Affects: `src/agents/story_finder/agent.py`, `src/agents/script_writer/agent.py`, `src/agents/script_writer/prompts.py`
- Requires: Schema updates and dynamic prompt selection logic.

**Effort Estimate:**
- Medium (1-2 days)

---

## Problem Description

### Current State
**Status:** Feature Request
**What's happening:**
The script writer produces generic or low-quality stories. It uses a single prompt for all story types.

**Desired State:**
- The `StoryFinder` should tag stories (e.g., "Educational", "News", "Fiction").
- The `ScriptWriter` should use a specific, optimized prompt based on the assigned tag to generate higher quality, more relevant scripts.

---

## Requirements

### Functional Requirements
**FR-1: Story Tagging**
- `StoryFinderAgent` MUST identify and assign a `tag` or `style` to each generated story idea.

**FR-2: Dynamic Prompting**
- `ScriptWriterAgent` MUST select the appropriate system prompt based on the story's tag.
- Create distinct prompts for at least: Educational, News, and General/Fiction.

**FR-3: Quality Improvements**
- Update prompts to encourage "hooking" stories, specific details, and better narrative structure.

---

## Implementation Plan

### Phase 1: Schema & Story Finder
1.  **Update Models**: Add `tags` or `style` field to `StoryIdea` in `src/agents/story_finder/models.py`.
2.  **Update Story Finder**: Modify prompt in `src/agents/story_finder/prompts.py` to generate these tags.

### Phase 2: Script Writer
1.  **Create Prompts**: In `src/agents/script_writer/prompts.py`, create dictionary of prompts keyed by tag.
2.  **Update Agent**: In `src/agents/script_writer/agent.py`, implement logic to select the prompt based on the input story's tag.

---

## Verification Plan

### Manual Verification
1.  Generate stories and verify they have tags.
2.  Select an "Educational" story and generate a script.
3.  Verify the script reflects the educational style/structure.
4.  Select a "News" story and verify the script reflects a news reporting style.
