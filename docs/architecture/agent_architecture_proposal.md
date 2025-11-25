# Proposed Agent Architecture Refactor

## Objective

To reorganize the agent workflow by separating concerns, activating the **Director Agent**, and establishing a clear chain of command. This ensures each agent focuses on its core competency, leading to higher quality stories, scripts, and visuals.

## Proposed Workflow

```mermaid
graph TD
    User[User Input] --> StoryFinder[Story Finder Agent]
    StoryFinder -->|Story Concept| ScriptWriter[Script Writer Agent]
    ScriptWriter -->|VideoScript (Text Only)| Director[Director Agent]
    
    subgraph "Visual Pipeline"
        Director -->|DirectedScript (Visuals)| ImageGen[Image Gen Agent]
        Director -->|Effects/Transitions| Assembly[Video Assembly Agent]
    end
    
    subgraph "Audio Pipeline"
        ScriptWriter -->|Dialogue| Voice[Voice Agent]
    end
    
    ImageGen -->|Images| Assembly
    Voice -->|Audio| Assembly
    Assembly -->|Final Video| Output
```

## Agent Responsibilities (Proposed)

### 1. Story Finder Agent (`src/agents/story_finder`)
- **Role:** **The Researcher**.
- **Duty:** Finds compelling stories, facts, or news based on the user's topic.
- **Output:** A structured `StoryConcept` (Topic, Key Facts, Angle).
- **Change:** Must be the entry point of the pipeline.

### 2. Script Writer Agent (`src/agents/script_writer`)
- **Role:** **The Screenwriter**.
- **Duty:** Focuses purely on narrative, dialogue, and pacing.
- **Change:** 
    - **REMOVE:** Detailed image prompt engineering.
    - **KEEP:** Basic scene description (e.g., "A busy market").
    - **Output:** `VideoScript` with rich dialogue and high-level scene descriptions.

### 3. Director Agent (`src/agents/director`)
- **Role:** **The Visionary**.
- **Duty:** Translates the text script into a visual experience.
- **Change:** **ACTIVATE** this agent in the pipeline.
    - **Visuals:** Converts basic scene descriptions into detailed, style-consistent `image_prompts` (Visual Segments).
    - **Cinematography:** Decides `shot_type`, `camera_movement`, `lighting`.
    - **Effects:** Explicitly selects video effects (Zoom, Pan, Shake) based on the emotional beat.
    - **Output:** `DirectedScript`.

### 4. Image Gen Agent (`src/agents/image_gen`)
- **Role:** **The Cinematographer / Artist**.
- **Duty:** Executes the Director's vision.
- **Change:** Uses the *Director's* detailed prompts, not the Script Writer's.

### 5. Video Assembly Agent (`src/agents/video_assembly`)
- **Role:** **The Editor**.
- **Duty:** Assembles the final cut.
- **Change:** Applies the effects and transitions dictated by the **Director**.

## Implementation Plan

1.  **Refactor `DirectorAgent`**: Ensure it can accept the current `VideoScript` and output a `DirectedScript` that is compatible with downstream agents.
2.  **Update `ScriptWriter`**: Simplify prompts to focus on story.
3.  **Update `ImageGen`**: Modify to accept `DirectedScript` (or adapt `DirectedScript` to look like `VideoScript` with enhanced prompts).
4.  **Update `VideoAssembly`**: Modify to read effect/transition metadata from `DirectedScript`.
5.  **Orchestration**: Rewrite `src/api/routes/videos.py` to chain these agents correctly.

## Benefits
- **Better Stories:** Script Writer isn't distracted by visuals.
- **Better Visuals:** Director focuses solely on visual language and consistency.
- **Modular:** Easier to upgrade individual agents (e.g., swap the Director logic without breaking the Script Writer).
