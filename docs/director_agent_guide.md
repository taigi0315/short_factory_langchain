# Director Agent - Usage Guide

## Overview

The Director Agent transforms video scripts into cinematically directed shot lists with visual coherence, narrative flow, and emotional impact.

## Quick Start

```python
from src.agents.director import DirectorAgent
from src.models.models import VideoScript

# Initialize Director Agent
director = DirectorAgent()

# Analyze your script
directed_script = await director.analyze_script(your_script)

# Access cinematic direction
for directed_scene in directed_script.directed_scenes:
    print(f"Shot Type: {directed_scene.direction.shot_type}")
    print(f"Camera Movement: {directed_scene.direction.camera_movement}")
    print(f"Enhanced Prompt: {directed_scene.direction.enhanced_image_prompt}")
```

## What the Director Agent Does

### 1. Story Beat Identification
Analyzes your script to identify narrative beats:
- **Hook**: Attention-grabbing opening
- **Setup**: Context establishment
- **Development**: Core content delivery
- **Resolution**: Closure and wrap-up

### 2. Emotional Arc Mapping
Maps the emotional journey through your video, identifying:
- Emotional tone of each beat
- Peak emotional moment
- Overall emotional progression

### 3. Cinematic Direction Generation
For each scene, generates:
- **Shot Type**: extreme_wide, wide, medium, close_up, etc.
- **Camera Movement**: static, push_in, pan, tilt, etc.
- **Camera Angle**: eye_level, low, high, dutch
- **Lighting Mood**: bright, dramatic, soft, golden_hour, etc.
- **Composition**: rule_of_thirds, centered, symmetry, etc.

### 4. Visual Continuity
Ensures scenes connect visually:
- Shot progression (wide → medium → close-up)
- Camera movement flow
- Emotional transitions
- Narrative connections

### 5. Enhanced Prompts
Creates detailed prompts for image/video generation:
- **Enhanced Image Prompt**: Includes shot type, lighting, composition
- **Enhanced Video Prompt**: Includes camera work, purpose, emotional journey

## Output Structure

```python
DirectedScript {
    original_script: VideoScript
    directed_scenes: List[DirectedScene]
    visual_theme: str
    emotional_arc: str
    pacing_notes: str
    director_vision: str
}

DirectedScene {
    original_scene: Scene
    direction: CinematicDirection
    story_beat: str
}

CinematicDirection {
    shot_type: ShotType
    camera_movement: CameraMovement
    camera_angle: CameraAngle
    lighting_mood: LightingMood
    composition: CompositionRule
    emotional_purpose: str
    narrative_function: str
    connection_from_previous: str
    connection_to_next: str
    enhanced_image_prompt: str
    enhanced_video_prompt: str
    director_notes: str
}
```

## Example Output

```
Scene 1 - Hook (Mystery Introduction):
  Shot Type: medium_close_up
  Camera: slow_push_in
  Angle: low
  Lighting: dramatic
  Composition: rule_of_thirds
  
  Emotional Purpose: Build tension and intrigue
  Narrative Function: Hook viewer with mystery
  
  Connection to Next: Sets up reveal by building tension
  
  Enhanced Image Prompt:
  "Medium close-up of character, positioned on left third, 
   dramatic side lighting creating shadows, mysterious expression, 
   slightly low angle suggesting hidden knowledge. 
   Photorealistic, professional photography, 8k uhd."
  
  Enhanced Video Prompt:
  "Start: Character's face in shadow, mysterious expression.
   Action: Slow push-in over 5 seconds, light gradually reveals face.
   Emotion: Building intrigue and tension.
   Purpose: Hook viewer with mystery, set up for revelation.
   Camera: Smooth dolly push-in, slight upward drift.
   End: Tight on eyes, ready for cut to wide reveal."
```

## Testing

Run the test script:
```bash
python scripts/test_director_agent.py
```

## Integration with Video Generation

The Director Agent sits between ScriptWriter and media generation:

```
ScriptWriter → Director Agent → ImageGen/VideoGen
```

Enhanced prompts from the Director Agent are used to generate:
- More cinematic images
- Better camera movements
- Stronger visual storytelling

## Next Steps

1. Test with your scripts
2. Review generated directions
3. Integrate with video generation pipeline
4. Iterate based on results
