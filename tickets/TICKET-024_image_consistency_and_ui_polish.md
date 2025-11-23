# TICKET-024: Image Style Consistency & UI Polish

## 🎯 Overview
Improve the visual consistency of generated videos by enforcing a global image style across all scenes. Also includes UI polish for the manual workflow and default settings.

## 📋 Requirements

### 1. Image Style Consistency
**Problem:** Currently, each scene's image prompt is generated independently, leading to disjointed visual styles (e.g., one scene is "cinematic", next is "cartoon").
**Solution:** 
- The `ScriptWriterAgent` should define a **Global Visual Style** for the entire video.
- This style should be prepended or enforced in every scene's `image_create_prompt`.

**Implementation:**
- Update `VideoScript` model to add `global_visual_style` (str).
- Update `ScriptWriterAgent` prompt to generate this style based on the story/genre.
- Ensure individual scene prompts inherit this style (e.g., "In a [global_style] style, [scene_specific_details]").

### 2. UI Defaults ("Auto" Mode)
**Problem:** Users have to manually select Mood and Category.
**Solution:** 
- Default Mood and Category to "Auto".
- If "Auto" is selected, the `StoryFinderAgent` should determine the best fit based on the input topic.

### 3. Manual Mode UI Polish
**Problem:** The "Effect" dropdown in the scene editor appears as a blank white box or is unclear.
**Solution:**
- Ensure the Effect dropdown has a clear default value (e.g., "Ken Burns (Zoom In)").
- Add a label or placeholder if needed so it's not empty.

## 🏗️ Technical Tasks

### Backend
- [ ] Modify `VideoScript` model in `src/models/models.py` to add `global_visual_style`.
- [ ] Update `ScriptWriterAgent` in `src/agents/script_writer/agent.py` to generate `global_visual_style`.
- [ ] Update `ScriptWriterAgent` prompt to ensure scene prompts reference the global style.
- [ ] (Optional) Update `StoryFinderAgent` to handle "Auto" mood/category logic if strictly needed, or just let the LLM decide based on topic.

### Frontend
- [ ] Update `frontend/src/app/page.tsx`:
    - Set default `mood` state to 'Auto'.
    - Set default `category` state to 'Auto'.
    - Add 'Auto' options to the dropdowns.
- [ ] Update `frontend/src/components/EffectSelector.tsx`:
    - Ensure it renders with a valid default value.
    - Fix styling if it looks like a "blank white box".

## 📅 Estimated Effort
- **Backend:** 1 day
- **Frontend:** 0.5 days

## 🔗 Dependencies
- TICKET-023 (Completed)
